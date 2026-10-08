"""ReLu-opptak med LeRobot.

  p = start opptak    s = stopp og lagre    r = forkast opptaket
  y = siste var suksess    n = siste mislyktes    q = avslutt

Eksempel:
  python relu_record.py --station stations/s1.yaml --repo-id relu-lab/pick_cube \\
      --task "Plukk opp kuben og legg den i boksen" --operator "Lars Olav"
"""

import argparse
import json
import os
import queue
import threading
import time
from datetime import datetime
from pathlib import Path

import yaml
from lerobot.cameras import CameraConfig
from lerobot.datasets import (
    LeRobotDataset,
    VideoEncodingManager,
    aggregate_pipeline_dataset_features,
    create_initial_features,
)
from lerobot.processor import make_default_processors
from lerobot.robots import RobotConfig, make_robot_from_config
from lerobot.scripts.lerobot_record import record_loop  # registrerer også alle arm- og kameratyper
from lerobot.teleoperators import TeleoperatorConfig, make_teleoperator_from_config
from lerobot.utils.feature_utils import combine_feature_dicts


def start_keys(on_key):
    """Leser enkelttaster fra terminalen (virker også over SSH). Returnerer en stopp-funksjon."""
    if os.name == "nt":  # Windows
        import msvcrt

        running = True

        def loop():
            while running:
                if msvcrt.kbhit():
                    on_key(msvcrt.getwch().lower())
                else:
                    time.sleep(0.02)

        threading.Thread(target=loop, daemon=True).start()

        def stop():
            nonlocal running
            running = False

        return stop

    from lerobot.utils.keyboard_input import TerminalKeyListener  # Linux / Mac / SSH

    listener = TerminalKeyListener(lambda key: on_key(key.lower()))
    listener.start()
    return listener.stop


def make_devices(station):
    """Lager robot og leader-arm fra stasjonsfila (samme typenavn som i lerobot-record)."""
    robot = dict(station["robot"])
    teleop = dict(station["teleop"])
    cameras = {}
    for name, cam in (robot.pop("cameras", None) or {}).items():
        cam = dict(cam)
        cameras[name] = CameraConfig.get_choice_class(cam.pop("type", "opencv"))(**cam)
    robot_cfg = RobotConfig.get_choice_class(robot.pop("type"))(cameras=cameras, **robot)
    teleop_cfg = TeleoperatorConfig.get_choice_class(teleop.pop("type"))(**teleop)
    return make_robot_from_config(robot_cfg), make_teleoperator_from_config(teleop_cfg)


def save_metadata(path, episodes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in episodes), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--station", required=True, help="f.eks. stations/s1.yaml")
    parser.add_argument("--repo-id", required=True, help="f.eks. relu-lab/pick_cube")
    parser.add_argument("--task", required=True, help="kort beskrivelse av oppgaven")
    parser.add_argument("--operator", required=True, help="hvem som styrer armen")
    parser.add_argument("--max-episode-s", type=float, default=120, help="lagres automatisk etter så mange sekunder")
    parser.add_argument("--push", action="store_true", help="last opp til Hugging Face når du avslutter")
    args = parser.parse_args()

    # --- Oppsett ---
    station = yaml.safe_load(Path(args.station).read_text(encoding="utf-8"))
    fps = station.get("fps", 30)
    robot, teleop = make_devices(station)
    teleop_proc, robot_proc, obs_proc = make_default_processors()
    features = combine_feature_dicts(
        aggregate_pipeline_dataset_features(
            pipeline=teleop_proc, initial_features=create_initial_features(action=robot.action_features)
        ),
        aggregate_pipeline_dataset_features(
            pipeline=obs_proc, initial_features=create_initial_features(observation=robot.observation_features)
        ),
    )
    repo_id = f"{args.repo_id}_{datetime.now():%Y%m%d_%H%M%S}"  # nytt navn hver økt, ingenting overskrives
    dataset = LeRobotDataset.create(
        repo_id, fps, robot_type=robot.name, features=features, image_writer_threads=4 * len(robot.cameras)
    )
    metadata_path = Path(dataset.root) / "relu" / "episodes.jsonl"
    episodes = []  # metadata om hver lagrede episode

    # --- Tastatur: tasten legges i en kø, og robot-løkka avbrytes ---
    keys = queue.Queue()
    events = {"exit_early": False, "rerecord_episode": False, "stop_recording": False}
    recording = False

    def on_key(key):
        if recording and key not in ("s", "r", "q"):
            return  # andre taster ignoreres under opptak
        keys.put(key)
        events["exit_early"] = True

    loop_args = dict(
        robot=robot, teleop=teleop, fps=fps, events=events, single_task=args.task,
        teleop_action_processor=teleop_proc, robot_action_processor=robot_proc,
        robot_observation_processor=obs_proc,
    )

    teleop.connect()
    robot.connect()
    stop_keys = start_keys(on_key)
    print(__doc__)
    print(f"Klar: stasjon {station['station']}, datasett {repo_id}. Trykk p for å starte.")

    try:
        with VideoEncodingManager(dataset):
            while True:
                # Venter: leader styrer follower, ingenting tas opp
                record_loop(control_time_s=float("inf"), **loop_args)
                key = keys.get()

                if key == "q":
                    break
                if key in ("y", "n") and episodes:
                    episodes[-1]["outcome"] = "success" if key == "y" else "failure"
                    save_metadata(metadata_path, episodes)
                    print(f"Episode {episodes[-1]['episode_index']} markert som {episodes[-1]['outcome']}.")
                if key != "p":
                    continue

                # Opptak
                while not keys.empty():  # glem taster trykket før p
                    keys.get()
                events["exit_early"] = False
                recording = True
                started_at = datetime.now().astimezone()
                print(f"● Tar opp episode {dataset.num_episodes}  (s = lagre, r = forkast)")
                record_loop(dataset=dataset, control_time_s=args.max_episode_s, **loop_args)
                recording = False
                key = "s" if keys.empty() else keys.get()  # tom kø = tiden gikk ut, lagre

                if key in ("r", "q"):
                    dataset.clear_episode_buffer()
                    print("✖ Opptak forkastet.")
                    if key == "q":
                        break
                    continue
                if not dataset.has_pending_frames():
                    continue

                frames_before = dataset.num_frames
                index = dataset.num_episodes
                dataset.save_episode()
                episodes.append({
                    "episode_index": index,
                    "task": args.task,
                    "operator": args.operator,
                    "station": station["station"],
                    "location": station.get("location"),
                    "robot_id": station["robot"].get("id"),
                    "outcome": "unknown",
                    "started_at": started_at.isoformat(timespec="seconds"),
                    "duration_s": round((datetime.now().astimezone() - started_at).total_seconds(), 1),
                    "num_frames": dataset.num_frames - frames_before,
                })
                save_metadata(metadata_path, episodes)
                print(f"✔ Episode {index} lagret. Trykk y (suksess) eller n (mislyktes), eller p for neste.")
    finally:
        stop_keys()
        if dataset.has_pending_frames():
            dataset.clear_episode_buffer()
        dataset.finalize()
        if robot.is_connected:
            robot.disconnect()
        if teleop.is_connected:
            teleop.disconnect()

    print(f"Ferdig: {len(episodes)} episoder lagret i {dataset.root}")
    if args.push and episodes:
        dataset.push_to_hub(tags=["relu", f"station-{station['station']}"])


if __name__ == "__main__":
    main()
