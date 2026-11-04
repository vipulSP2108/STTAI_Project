# 3-Minute Video Screencast Demonstration Script
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR with Drift-Triggered Retraining
# IIT Gandhinagar (2026-27)
# Video File: supporting_files/screen_recording.mp4 (Duration: 3 minutes / 180 seconds)

---

## Video Walkthrough Overview
This recording provides an unbroken, authentic demonstration of the containerized voice helpdesk service, offline execution under `--network none`, real-time speech routing, streaming drift detection, and closed-loop retraining safety gating.

---

### Phase 1: Docker Offline Validation & Checksum Assertion (0:00 – 0:45)
- **Visual**: Terminal terminal executing on local CPU machine with internet disconnected.
- **Narrator (Rajdeep Vraj)**:
  > *"Welcome to the live demonstration of Project 5: Cross-Lingual Institute Voice Helpdesk ASR. We begin by demonstrating strict offline compliance required by Part D. The container is executed with `--network none` to assert zero outbound network communication."*
- **Terminal Command**:
  ```bash
  docker run --rm --network none voice-helpdesk-asr:a2-final validate
  ```
- **Observed Behavior**:
  - Validates `data/gold_test_set.csv` SHA-256 matches `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`.
  - Runs local CPU inference across all 29 held-out gold audio clips.
  - Outputs formatted JSON results matching report metrics:
    `WER: 1.5411`, `CER: 1.2178`, `Intent Accuracy: 0.4483`, `RTF: 0.174`.
  - Writes `supporting_files/offline_validation_output.json`.

---

### Phase 2: Live Streamlit UI & FastAPI Microservice (0:45 – 1:30)
- **Visual**: Web browser opening `http://localhost:8501`.
- **Narrator (Vipul Sunil Patil)**:
  > *"Next, we start the interactive Streamlit dashboard and FastAPI service on local port 8501. The interface allows users to select pre-bundled consented voice queries or upload spontaneous student audio."*
- **Demonstration Steps**:
  1. User selects bundled query: *Admissions: GATE Cutoff Inquiry (P6)*.
  2. Plays audio waveform.
  3. Clicks **Process Voice Query**.
  4. Real-time CPU Whisper base speech recognition generates verbatim transcript:
     *"Namaste sir, I am here for my girl's admission..."*
  5. Neural routing head classifies intent as `ADMISSIONS` with 94.2% confidence.
  6. Real-Time Factor (RTF) displayed as `0.17` (well under the 1.0 real-time threshold).
  7. Inspects `/health` and `/version` endpoints confirming `a2-final` commit and `production` model version.

---

### Phase 3: Online Traffic Monitoring & Drift Telemetry (1:30 – 2:15)
- **Visual**: Running `traffic_replay.py` terminal and viewing `supporting_files/plots/drift_detection_plot.png`.
- **Narrator (Satvik Sharma)**:
  > *"In Part E, we simulate production traffic shifting gradually from in-domain campus speakers to shifted regional accents (Cohort B: Maharashtra). We track two label-free signals: predictive softmax entropy and audio SNR."*
- **Terminal Command**:
  ```bash
  python code/a2_part_e_monitoring/traffic_replay.py
  ```
- **Observed Behavior**:
  - Validation baseline entropy: `1.245 nats`.
  - Calibrated drift alarm threshold: `1.310 nats`.
  - Batches 1 to 4 show stable in-domain traffic.
  - At Batch 5 (100% Cohort B shift), predictive entropy climbs to `1.321 nats`, crossing the threshold and triggering:
    `🚨 DRIFT ALERT! Retraining Dispatched`.
  - Zero false alarms on in-domain validation data (0.0%).

---

### Phase 4: Automated Active Retraining & Gating Logic (2:15 – 3:00)
- **Visual**: Terminal executing `retrain_pipeline.py` and reviewing `TEST_SET_LOG.md`.
- **Narrator (All Members)**:
  > *"Upon drift alarm, the closed-loop retraining pipeline is dispatched. It acquires the 16 highest-entropy queries from Cohort B via active learning uncertainty sampling, asserts zero test leakage, and retrains the intent classifier."*
- **Demonstration Steps**:
  1. Run standard retraining:
     ```bash
     python code/a2_part_e_monitoring/retrain_pipeline.py --mode standard
     ```
     - Cohort B accuracy improves from 37.5% to 56.2% (+18.8%).
     - Gold test accuracy regresses by 3.4% (> 2.0% advance tolerance).
     - **Gate Decision**: `⚠️ REJECTED & ROLLBACK` (protects production!).
  2. Run conservative regularized retraining:
     ```bash
     python code/a2_part_e_monitoring/retrain_pipeline.py --mode conservative
     ```
     - Cohort B accuracy improves to 46.9% (+9.4%).
     - Gold test accuracy preserved at 44.8% (0.0% degradation $\le 2.0\%$).
     - **Gate Decision**: `🎉 PROMOTED TO PRODUCTION` (`candidate-retrained-v2`).
  3. Inspects `TEST_SET_LOG.md` showing cryptographically verified audit records.

---

## Verifiable Video File
- Path: `supporting_files/screen_recording.mp4`
- Duration: 180 seconds (3:00)
- Format: MP4 (H.264 video, AAC audio, 1920x1080 Full HD)
