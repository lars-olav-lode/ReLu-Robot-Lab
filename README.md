# ReLu-Robot-Lab

Oppsett, kalibrering og skript for ReLu sine SO-101-stasjoner (leader + follower, LeRobot).

Koden for LeRobot ligger i forken [LabReLUPhysucalHF](https://github.com/lars-olav-lode/LabReLUPhysucalHF) (basert på Hiwonder sin SO-ARM101-versjon). Dette repoet inneholder bare det som er spesifikt for laben vår.

---

## Stasjoner

| Stasjon | Plassering | Follower-id | Leader-id | Kameraer |
|---|---|---|---|---|
| **Stasjon 1** (`s1`) | Ved vinduene | `follower_s1` | `leader_s1` | `front` (bord) + `wrist` (håndledd) |
| **Stasjon 2** (`s2`) | _fyll inn_ | `follower_s2` | `leader_s2` | `front` (bord) + `wrist` (håndledd) |

> ⚠️ **Hver arm har sin egen kalibreringsfil.** Bruk alltid id-en til stasjonen du står ved. Feil kalibrering får follower-armen til å gå til feil posisjoner og kan kjøre den inn i endestopp.

Armene er merket fysisk med id-en sin. Bytt aldri armer mellom stasjoner uten å kalibrere på nytt.

---

## Mappestruktur

```
ReLu-Robot-Lab/
├── README.md
├── environment.yml
├── calibration/
│   ├── robots/so101_follower/        # follower_s1.json, follower_s2.json
│   └── teleoperators/so101_leader/   # leader_s1.json, leader_s2.json
└── scripts/
    ├── teleop.sh          # teleoperasjon med kameraer
    ├── record.sh          # opptak av datasett
    ├── reset_leader.py    # nullstiller homing offsets på leader
    └── check_m5.py        # feilsøking av motor 5 (wrist_roll)
```

---

## 1. Installasjon (Windows, Mac og Linux)

Kjør alt **direkte på maskinen**, ikke i VM eller WSL. USB-videresending til armene er ustabil der.

**Windows:** bruk Git Bash + Miniconda.
**Mac/Linux:** vanlig terminal + Miniconda.

```bash
# 1. Klon begge repoene
git clone https://github.com/lars-olav-lode/LabReLUPhysucalHF.git
git clone https://github.com/lars-olav-lode/ReLu-Robot-Lab.git

# 2. Lag miljøet (Python 3.12 + ffmpeg)
cd ReLu-Robot-Lab
conda env create -f environment.yml
conda activate lerobot

# 3. Installer LeRobot fra forken
cd ../LabReLUPhysucalHF
pip install -e ".[feetech]"
```

> Sjekk `pyproject.toml` i forken om det finnes et `hiwonder`-extra. I så fall: `pip install -e ".[feetech,hiwonder]"`.

> **Intel-Mac:** det har vært versjonskonflikt med `torchvision`. Si fra i Slack hvis du får installasjonsfeil.

---

## 2. Drivere og porter

Kontrollerkortet på hver arm kobles til PC-en med USB-C og dukker opp som en seriell port.

### Drivere
- **Windows:** Hvis armen ikke dukker opp under *Enhetsbehandling → Porter (COM og LPT)*, installer **CH340/CH343-driveren** fra WCH (wch-ic.com) og koble til på nytt.
- **Mac:** Nyere macOS har driveren innebygd. Ser du ingen `/dev/tty.usbmodem*`, installer CH34x-driveren fra WCH.
- **Linux:** Ingen driver trengs, men brukeren må ha tilgang til porten:
  ```bash
  sudo usermod -aG dialout $USER   # logg ut og inn igjen etterpå
  ```

### Finn portene dine
Portene er **forskjellige på hver PC** og kan endre seg hvis du bytter USB-inngang. Sjekk dem hver gang du kobler til på en ny maskin:

```bash
lerobot-find-port
```

Følg instruksjonene (trekk ut USB-kabelen når den ber om det). Gjør det for begge armene.

| OS | Eksempel på port |
|---|---|
| Windows | `COM3`, `COM4` |
| Mac | `/dev/tty.usbmodem58760431541` |
| Linux | `/dev/ttyACM0`, `/dev/ttyACM1` |

Koble alltid til **strøm (12 V / 5 V) før** du kjører kommandoer. Uten strøm svarer ikke motorene selv om porten finnes.

---

## 3. Kameraer

Kameraindeksene er også forskjellige fra PC til PC.

```bash
lerobot-find-cameras opencv
```

Se på testbildene i `outputs/captured_images/` for å finne ut hvilket kamera som er `front` og hvilket som er `wrist`. Lukk Teams, Zoom og Kamera-appen før du kjører, ellers blir kameraene opptatt.

---

## 4. Teleoperasjon

Kjør fra rota av dette repoet. Sett stasjon, porter og kameraer med variabler:

```bash
STATION=s1 FOLLOWER_PORT=COM3 LEADER_PORT=COM4 CAM_FRONT=0 CAM_WRIST=2 bash scripts/teleop.sh
```

Eksempel på Mac:

```bash
STATION=s2 FOLLOWER_PORT=/dev/tty.usbmodem111 LEADER_PORT=/dev/tty.usbmodem222 CAM_FRONT=0 CAM_WRIST=1 bash scripts/teleop.sh
```

Rerun åpner seg og viser leddposisjoner og kamerastrømmer. Avslutt med `Ctrl+C`.

Spør programmet om kalibreringsfil, trykk **ENTER** for å bruke fila i repoet. Skriv **ikke** `c` med mindre du faktisk skal kalibrere på nytt.

---

## 5. Kalibrering (bare ved behov)

Kalibrer på nytt bare hvis en motor er byttet, et horn er skrudd av, eller armen oppfører seg feil.

```bash
# Leader
lerobot-calibrate --teleop.type=so101_leader --teleop.port=<PORT> --teleop.id=leader_s1 \
  --teleop.calibration_dir=calibration/teleoperators/so101_leader

# Follower
lerobot-calibrate --robot.type=so101_follower --robot.port=<PORT> --robot.id=follower_s1 \
  --robot.calibration_dir=calibration/robots/so101_follower
```

1. Flytt alle ledd til **midten** av bevegelsesområdet og trykk ENTER.
2. Beveg hvert ledd fra ytterpunkt til ytterpunkt. **wrist_roll** roteres en hel runde. Trykk ENTER.

**Commit alltid ny kalibrering** så de andre får den:

```bash
git add calibration && git commit -m "Rekalibrert leader_s1" && git push
```

---

## 6. Feilsøking

| Feilmelding | Årsak | Løsning |
|---|---|---|
| `command not found` med rare tegn (`$'\302\203...`) | Skjult tegn fra kopiering | Trykk `Ctrl+U`, skriv kommandonavnet for hånd |
| `Missing motor IDs: 5` | Motoren svarer ikke | Sjekk kablene ved motoren. Hjelper ikke det: `lerobot-setup-motors` og koble én motor om gangen |
| `Magnitude ... exceeds 2047` under kalibrering | Et ledd står ved encoderens nullpunkt | Kjør `scripts/reset_leader.py`, vri leddet ca. en halv runde og kalibrer igjen |
| `Mismatch between calibration values in the motor and the calibration file` | Feil id eller ny motor | Sjekk at id-en stemmer med stasjonen. Ellers kalibrer |
| Ingen COM-port / `ttyACM` | Driver eller strøm mangler | Se seksjon 2 |
| Kamera feiler ved oppstart | Feil indeks eller oppløsning, eller kameraet er i bruk | Kjør `lerobot-find-cameras opencv` på nytt |

---

## Regler

- **Ikke commit HF-tokens** eller passord. Bruk `huggingface-cli login` på egen maskin.
- Datasett lagres i **LeRobotDataset v3**-format og lastes opp til Hugging Face, ikke hit.
- Kontakt infra-ansvarlig (Lars Olav) ved spørsmål.
