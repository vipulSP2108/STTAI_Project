# Final Annotation Environments & Data Duration Report

This directory contains the dual Label Studio annotation setup and the audio corpus collected under the `Records/` directory, with newly segmented participant folders (`P13`, `P14`, `P16`, `P18`, `P19`) synchronized alongside the initial corpus (`P1`–`P12`, `P20`, `P21`, `P22`). Folders `P15` and `P17` remain unsegmented and excluded.

---

## 1. Directory Structure

```
final_annotation/
├── annotator_1/              # Label Studio Instance 1 (Lead Annotator A1)
│   ├── records/              # All 182 16kHz WAV recordings
│   ├── data/                 # Label Studio database and state
│   ├── start.sh              # Runner on Port 8081
│   └── label_studio.log      # Service logs
├── annotator_2/              # Label Studio Instance 2 (Secondary Annotator A2)
│   ├── records/              # All 182 16kHz WAV recordings
│   ├── data/                 # Label Studio database and state
│   ├── start.sh              # Runner on Port 8082
│   └── label_studio.log      # Service logs
├── records/                  # Master 16kHz mono WAV audio repository
├── label_studio_config.xml   # Standardized annotation interface XML
├── sync_records.py           # Automated sync script for adding new recordings
├── AUDIO_DATA_SUMMARY.json   # Machine-readable per-file and per-folder statistics
├── start_all.sh              # Starts both Label Studio instances in background
└── stop_all.sh               # Stops both running Label Studio instances
```

---

## 2. Active Label Studio Services

| Instance | Role | Web Interface | Login Credentials |
| :--- | :--- | :--- | :--- |
| **Annotator 1** | Lead Annotator (A1) | [http://localhost:8081](http://localhost:8081) | `Vipul.patil@iitgn.ac.in` / `annotator1password`<br>or `annotator1@institution.local` / `annotator1password` |
| **Annotator 2** | Secondary Annotator (A2) | [http://localhost:8082](http://localhost:8082) | `Vipul.patil@iitgn.ac.in` / `annotator1password`<br>or `annotator2@institution.local` / `annotator2password` |

---

## 3. Annotation Interface Features

The labeling schema follows the required two-step workflow:

1. **Large Audio Player**:
   - High-fidelity 16 kHz mono waveform with zoom slider, play/pause (spacebar shortcut), and seek bar.
   - Configured with `value="$audio"` and local storage binding.

2. **Step 1: Spoken Languages & Verbatim Transcript**:
   - **Language Multi-Choice Buttons / Checkboxes**:
     - `English` (Hotkey `e`)
     - `Hindi` (Hotkey `h`, हिन्दी)
     - `Gujarati` (Hotkey `g`, ગુજરાતી)
     - Annotators can select multiple languages for code-mixed speech (e.g. English + Hindi, English + Gujarati).
   - **Verbatim Transcript Area**:
     - Editable text area to type verbatim speech in code-mixed English / हिन्दी / ગુજરાતી.

3. **Step 2: Intent Classification**:
   - Single-choice radio selection with hotkeys:
     - `admissions` (Hotkey `1`)
     - `hostel_mess` (Hotkey `2`)
     - `it_support` (Hotkey `3`)
     - `student_services` (Hotkey `4`)

---

## 4. How to Add New Records

Whenever you add new recordings to `Records/` (e.g., adding `P23/`, or new files to `P21/`):

Simply run:
```bash
python3 final_annotation/sync_records.py
```

### What this script does automatically:
1. Scans `Records/` (including `1 clip 1 tar/` cuts and excluding unsegmented folders `P15`, `P17`).
2. Automatically converts any newly added audio files to 16 kHz mono `.wav` using `ffmpeg`.
3. Syncs the files to `final_annotation/records/`, `annotator_1/records/`, and `annotator_2/records/`.
4. Appends new tasks to both Annotator 1 and Annotator 2 databases **without deleting existing annotations or tasks**.
5. Re-notifies the running Label Studio daemons via REST API so they appear immediately in the UI.
6. Re-calculates and prints total audio duration statistics and updates `AUDIO_DATA_SUMMARY.json`.

*(Optional)* If you ever want to do a clean re-indexing of all records from scratch:
```bash
python3 final_annotation/sync_records.py --reset
```

---

## 5. Total Collected Data Duration

### Summary
- **Included Folders**: 20 folders (`P1`–`P14`, `P16`, `P18`–`P22`)
- **Excluded Folders**: 2 folders (`P15`, `P17`)
- **Total Audio Files**: **182 files** (108 initial + 74 newly cut)
- **Total Duration**: **6,560.31 seconds** (**1 hour, 49 minutes, 20.31 seconds**)

### Per-Folder Breakdown (Included)

| Participant Folder | File Count | Total Duration (Seconds) | Duration (Formatted) |
| :--- | :---: | :---: | :---: |
| **P1** | 2 | 102.87 s | 1m 42.87s |
| **P2** | 11 | 599.99 s | 9m 59.99s |
| **P3** | 3 | 184.04 s | 3m 04.04s |
| **P4** | 5 | 331.83 s | 5m 31.83s |
| **P5** | 6 | 381.46 s | 6m 21.46s |
| **P6** | 1 | 53.41 s | 0m 53.41s |
| **P7** | 9 | 530.46 s | 8m 50.46s |
| **P8** | 10 | 838.00 s | 13m 58.00s |
| **P9** | 10 | 504.21 s | 8m 24.21s |
| **P10** | 2 | 114.47 s | 1m 54.47s |
| **P11** | 4 | 274.87 s | 4m 34.87s |
| **P12** | 2 | 85.21 s | 1m 25.21s |
| **P13** | 22 | 227.93 s | 3m 47.93s |
| **P14** | 11 | 121.05 s | 2m 01.05s |
| **P16** | 14 | 128.37 s | 2m 08.37s |
| **P18** | 16 | 175.38 s | 2m 55.38s |
| **P19** | 11 | 115.76 s | 1m 55.76s |
| **P20** | 10 | 622.65 s | 10m 22.65s |
| **P21** | 18 | 365.32 s | 6m 05.32s |
| **P22** | 15 | 803.02 s | 13m 23.02s |
| **Total Included** | **182** | **6,560.31 s** | **1h 49m 20.31s** |
