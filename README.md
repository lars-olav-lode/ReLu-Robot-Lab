# ReLu-Robot-Lab

Oppsett, kalibrering og skript for ReLu sine SO-101-stasjoner (leader + follower, LeRobot).

Vi bruker den offisielle [LeRobot](https://github.com/huggingface/lerobot) fra Hugging Face. Dette repoet inneholder bare det som er spesifikt for laben vår.

---

## Stasjoner

> # 🚨 VELDIG VIKTIG: SJEKK HVILKEN STASJON DU STÅR VED
>
> | Stasjon | Plassering | Follower-id | Leader-id |
> |---|---|---|---|
> | **Stasjon 1** (`s1`) | **IKKE ved vinduene** | `follower_s1` | `leader_s1` |
> | **Stasjon 2** (`s2`) | **Ved vinduene** | `follower_s2` | `leader_s2` |
>
> **Står du ved vinduene → bruk `s2`. Står du ikke ved vinduene → bruk `s1`.**
>
> Hver arm har sin **egen** kalibreringsfil. Bruker du feil stasjon, laster du inn kalibreringen til en annen arm. Da går follower-armen til feil posisjoner og kan kjøre inn i endestoppene og skade motorene.

Begge stasjonene har to kameraer: `front` (bord) og `wrist` (håndledd).

Armene skal være merket fysisk med id-en sin. Bytt aldri armer mellom stasjoner uten å kalibrere på nytt.

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
    └── record.sh          # opptak av datasett
```

---

## 1. Installasjon (Windows, Mac og Linux)

Kjør alt **direkte på maskinen**, ikke i VM eller WSL. USB-videresending til armene er ustabil der.

**Windows:** bruk Git Bash + Miniconda.
**Mac/Linux:** vanlig terminal + Miniconda.

```bash
# 1. Klon begge repoene
git clone https://github.com/huggingface/lerobot.git
git clone https://github.com/lars-olav-lode/ReLu-Robot-Lab.git

# 2. Lag miljøet (Python 3.12 + ffmpeg)
cd ReLu-Robot-Lab
conda env create -f environment.yml
conda activate lerobot

# 3. Installer LeRobot (låst versjon, se under)
cd ../lerobot
git checkout ca69a2068462a37f7cdcb74180927a2f863d2bf7
pip install -e ".[feetech,viz]"   # feetech = motorene, viz = Rerun-visning
```

> **Låste versjoner:** Python 3.12 og ffmpeg 7.1.1 (i `environment.yml`) og LeRobot på commit `ca69a20`. Ikke bruk nyeste `main` fra LeRobot. Nye versjoner kan endre kalibreringsformatet og kommandoene. Oppgraderinger gjøres samlet av infra-ansvarlig, etter test på begge stasjonene.

> ⚠️ **Intel-Mac (fra før 2020) støttes ikke.** PyTorch lager ikke lenger nye versjoner for Intel-Mac, så installasjonen feiler med versjonskonflikt på `torch`/`torchvision`. Bruk en Windows-PC, Linux-PC eller Mac med Apple-chip (M1–M4).

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

> 💡 **Svarer ikke motorene?** Ta ut strømkabelen til armen, vent **5 sekunder** og sett den i igjen. Da startes alle motorene på nytt, og det løser ofte problemet. Prøv dette først før du feilsøker videre.

| Feilmelding | Årsak | Løsning |
|---|---|---|
| `command not found` med rare tegn (`$'\302\203...`) | Skjult tegn fra kopiering | Trykk `Ctrl+U`, skriv kommandonavnet for hånd |
| `Missing motor IDs: 5` | Motoren svarer ikke | Ta ut strømmen i 5 sekunder. Sjekk så kablene ved motoren. Hjelper ikke det: `lerobot-setup-motors` og koble én motor om gangen |
| `Magnitude ... exceeds 2047` under kalibrering | Et ledd står ved encoderens nullpunkt (ofte wrist_roll) | Vri leddet ca. en halv runde før du trykker ENTER i midtposisjon. Hjelper ikke det: kontakt infra-ansvarlig |
| `Missing motor IDs` for **alle** motorene | Armen har ikke strøm, eller feil port | Ta ut strømmen i 5 sekunder og sett den i igjen. Sjekk så at adapteren står i, og kjør `lerobot-find-port` |
| `Mismatch between calibration values in the motor and the calibration file` | Feil id eller ny motor | Sjekk at id-en stemmer med stasjonen. Ellers kalibrer |
| Ingen COM-port / `ttyACM` | Driver eller strøm mangler | Se seksjon 2 |
| Kamera feiler ved oppstart | Feil indeks eller oppløsning, eller kameraet er i bruk | Kjør `lerobot-find-cameras opencv` på nytt |

---

## Regler

- **Ikke commit HF-tokens** eller passord. Bruk `huggingface-cli login` på egen maskin.
- Datasett lagres i **LeRobotDataset v3**-format og lastes opp til Hugging Face, ikke hit.
- Kontakt infra-ansvarlig (Lars Olav) ved spørsmål.
