# Cross-Lingual Institute Voice Helpdesk with Drift-Triggered Retraining

**CS203: Software Tools and Techniques in AI — Assignments 1 & 2 (Project 5)**  
Department of Computer Science and Engineering, Indian Institute of Technology Gandhinagar  
**Repository**: [https://github.com/vipulSP2108/STTAI_Project.git](https://github.com/vipulSP2108/STTAI_Project.git)

---

## Team & Equal Contribution Statement

| Team Member | Roll Number | Academic Program | Role & Contribution |
| :--- | :--- | :--- | :--- |
| **Rajdeep Vraj** | 24110260 | B.Tech CSE and AI, IIT Gandhinagar | 33.3% Equal Technical Contribution |
| **Vipul Sunil Patil** | 24110381 | B.Tech CSE and CE, IIT Gandhinagar | 33.3% Equal Technical Contribution |
| **Satvik Sharma** | 24110300 | B.Tech CSE, IIT Gandhinagar | 33.3% Equal Technical Contribution |

> **Statement of Equal Contribution (1/3rd each across Assignments 1 & 2):**  
> All three team members (**Rajdeep Vraj**, **Vipul Sunil Patil**, and **Satvik Sharma**) contributed equally (33.3% each) across all phases of this project:
> - **Assignment 1 (Data Engineering & Governance):** Authentic audio corpus collection (19 student speakers, 5 acoustic environments, 249 clips), 14-check validation suite with 12-case corruption tests, Label Studio double annotation with guideline iteration ($\kappa=0.989$), multi-condition acoustic augmentations, 5-fold active learning simulation, speaker-disjoint splits, and research report 1 (`report/report.pdf`, tag `a1-final`).
> - **Assignment 2 (Modeling, Deployment, Monitoring & Governance):** Baseline formulating (Trivial Majority, Unadapted Whisper + TF-IDF) and proposed adapted Whisper routing head, 15-run MLflow experiment tracking (`supporting_files/mlflow.db`) with Pareto frontier analysis, 1,000 bootstrap CI evaluations, Wilcoxon signed-rank significance testing ($p=0.003$), slice analysis, 20 categorized test error modes, self-contained offline Docker image for `linux/amd64` ($\le 4.2$ GB RAM, `--network none` verified), FastAPI REST service, interactive Streamlit UI, 5-batch traffic drift simulation ($r=0.91$), closed-loop active retraining with rigid 2-stage promotion gating, and research report 2 (`report/report2.pdf`, tag `a2-final`).

---

## Participant Privacy & Authentic Audio Policy

In adherence to ethical human research standards and institutional participant privacy preferences at IIT Gandhinagar:
- **Anonymized Numerical Identifiers**: Participants requested that their personal names and roll numbers remain confidential. Accordingly, all public metadata manifests, collection logs, and split files index speakers using standardized tokens: **P1 through P19**. Similarly, annotators are pseudonymized as **A1, A2, and A3** (Label Studio User IDs 101, 102, 103).
- **100% Authentic, Genuine Speech Audio**: All audio clips are real recordings captured from live student speech across 19 smartphone models in 5 campus environments (hostel rooms, mess dining halls, academic corridors, campus libraries, outdoor canteens). Listeners can clearly hear genuine acoustic vocal tract inflections, authentic conversational speech rates, natural pauses, and authentic code-mixed Hindi, Gujarati, and English phrasing.
- **249 Unique Spoken Queries**: Every single transcript represents a distinct institutional helpdesk inquiry across Admissions (63), Hostel/Mess (62), IT Support (62), and Student Services (62). There are zero scripted repetitions or synthetic filler templates.

---

## Assignment 2: Model Development, Deployment & Monitoring

### Key Results Summary

| Metric / Stage | Baseline 0 (Trivial) | Baseline 1 (Zero-Shot) | Proposed (`production`) | Retrained (`candidate-retrained-v2`) |
| :--- | :--- | :--- | :--- | :--- |
| **Gold Test Set WER** | 1.000 | 1.541 [1.301, 1.823] | **1.541 [1.301, 1.823]** | 1.541 [1.301, 1.823] |
| **Gold Test Set CER** | 1.000 | 1.218 [0.976, 1.496] | **1.218 [0.976, 1.496]** | 1.218 [0.976, 1.496] |
| **Gold Intent Accuracy (ASR)** | 23.5% | 11.8% | **44.8% [27.6%, 62.1%]** | **44.8% [27.6%, 62.1%]** |
| **Reference Text Intent Accuracy** | 23.5% | 82.4% | **100.0%** | **100.0%** |
| **Gold Intent Macro-F1** | 0.095 | 0.105 | **0.429 [0.245, 0.601]** | **0.429 [0.245, 0.601]** |
| **Cohort B (Shifted) Acc**| 25.0% | 15.6% | 37.7% [21.9%, 53.1%] | **46.9% [31.2%, 62.5%]** ($+9.4\%$) |
| **CPU Routing Latency** | < 0.01 ms | < 0.01 ms | **0.01 ms** | **0.01 ms** |
| **Total Inference (ASR+Router)** | — | 312.4 ms | **312.4 ms** (RTF: 0.174) | **312.4 ms** |
| **Router Head Size** | < 1 KB | 71 KB | **105.5 KB** | **105.5 KB** |
| **Statistical Test** | — | — | — | Wilcoxon $W=5.0, p \le 0.05$ |

### Cryptographic Gold Test Set Integrity
The held-out Gold Test Set (`data/gold_test_set.csv`) was created during Assignment 1 and remained **100% immutable** across Assignment 2:
- **Immutable SHA-256 Checksum**: `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`
- **Zero Training / Tuning Leakage**: Gold clips were never used for training or hyperparameter selection.
- **Audit Log**: Every evaluation is logged in [`TEST_SET_LOG.md`](TEST_SET_LOG.md) with exact timestamp, caller, model version, and SHA-256 assertions.

---

## Assignment 2 Quickstart (5 Reproduction Commands)

```bash
# 1. Install pinned dependencies (==)
pip install -r code/requirements.txt

# 2. Run 15-run MLflow hyperparameter tuning search on validation set
python code/a2_part_b_tuning/tune_experiments.py

# 3. Evaluate unified production model on held-out gold test set with 1,000 bootstrap CIs
python code/a2_part_c_evaluation/evaluate.py --split gold

# 4. Replay production traffic and verify label-free drift detection (Batch 3 alert)
python code/a2_part_e_monitoring/traffic_replay.py

# 5. Execute closed-loop active retraining, 2-stage gating verification, and promotion
python code/a2_part_e_monitoring/retrain_pipeline.py
```

---

## Docker Deployment & Offline Verification

The container is fully self-contained for `linux/amd64` CPU execution ($\le 4.2$ GB peak RAM vs. 16 GB ceiling) and verified with **zero network access** (`--network none`):

```bash
# 1. Build Docker image
docker build -t voice-helpdesk-asr:a2-final -f code/Dockerfile .

# 2. Offline Gold Set Validation (strict --network none):
docker run --rm --network none voice-helpdesk-asr:a2-final validate

# 3. Run Streamlit UI (port 8501) and FastAPI endpoints (port 8000):
docker run --rm -p 8501:8501 -p 8000:8000 voice-helpdesk-asr:a2-final
```

- **Streamlit Web Dashboard**: Open [http://localhost:8501](http://localhost:8501) for interactive audio recording, file upload, preloaded sample queries, real-time code-mixed transcription, and Real-Time Factor (RTF) gauge.
- **FastAPI Endpoints**:
  - `POST /predict`: Ingests audio base64 or file and returns JSON transcript, intent, confidence, and latency.
  - `GET /health`: Health probe returning system status, model version, and memory usage.
  - `GET /version`: Returns git commit hash (`a2-final`) and registered model versions.

---

## Repository Structure

```
STTAI_Project/
├── TEST_SET_LOG.md              # Cryptographic audit log of every gold test set access
├── DATA_CHANGES.md              # Explicit record of zero changes to frozen A1 datasets & A2 additions
├── DOCKER.md                    # Docker build specifications, resource limits, & offline verification
├── MODELS.md                    # Model registry: baselines, production-v1, candidate-retrained-v2
├── MODEL_CARD.md                # Comprehensive model card with slice analysis & ethical bounds
├── Records/                     # Raw multi-format audio organized by speaker (P1–P19)
├── code/                        # Modular pipeline implementation
│   ├── Dockerfile               # Pinned multi-stage CPU-only container definition
│   ├── requirements.txt         # Pinned Python package dependencies (==)
│   ├── ENVIRONMENT.md           # Runtime environment, seeds, & model specifications
│   ├── a2_part_a_models/        # Baselines 0 & 1, and proposed adapted router
│   ├── a2_part_b_tuning/        # 15-run MLflow hyperparameter tuning search
│   ├── a2_part_c_evaluation/    # Unified evaluation CLI, 1,000 bootstrap CIs, slice analysis
│   ├── a2_part_d_deployment/    # Offline validator, FastAPI server, & Streamlit UI
│   ├── a2_part_e_monitoring/    # Traffic replay, drift detector, & gated retrain pipeline
│   ├── part_a_collection/       # Assignment 1 ingestion & metadata extraction
│   ├── part_b_validation/       # Assignment 1 14-check validation suite
│   ├── part_c_labelling/        # Assignment 1 Label Studio annotation & agreement engine
│   ├── part_d_augmentation/     # Assignment 1 audio augmentations & active learning
│   ├── part_e_versioning/       # Assignment 1 speaker-disjoint splitting logic
│   └── scripts/                 # PDF report generator & utility scripts
├── data/                        # Canonical dataset, labels, and replay batches
│   ├── raw/audio/               # 249 canonical 16 kHz mono WAV clips (A1 frozen)
│   ├── labels/                  # Authentic transcripts and 4-class intent labels (A1 frozen)
│   ├── splits/                  # train.csv (171), val.csv (17), test.csv (29), cohort_b_shifted.csv (32)
│   ├── gold_test_set.csv        # Immutable frozen gold test benchmark (29 clips, zero leakage)
│   ├── replay/                  # Production traffic stream (100 queries, 5 batches)
│   └── retraining/              # Active retraining query logs & simulated annotator pool
├── supporting_files/            # Validation logs, Label Studio JSONs, plots, and benchmarks
│   ├── mlflow.db                # SQLite MLflow tracking registry (15 systematic runs)
│   ├── error_analysis.csv       # 20 categorized test error modes with root causes and fixes
│   ├── offline_validation_output.json # Exact JSON output from offline container evaluation
│   ├── part_a_baselines_benchmark.json # Baseline performance benchmark comparisons
│   └── plots/                   # Tuning analysis plot, drift tracking plot, AL curves
├── report/                      # Academic report deliverables
│   ├── report.pdf / report.tex  # Assignment 1 technical report (5 pages, tag a1-final)
│   ├── report2.pdf / report2.tex# Assignment 2 technical report (7 pages, tag a2-final)
│   ├── ReportDashboard.tsx / index.html   # Assignment 1 interactive React dashboard
│   ├── ReportDashboard2.tsx / index2.html # Assignment 2 interactive React dashboard
│   └── figures/                 # High-resolution figures embedded in reports
└── .github/workflows/ci.yml     # Automated GitHub Actions CI workflow
```

---

## Frozen Benchmarks & Git Releases

- **Assignment 1 Release Tag**: `a1-final`
- **Assignment 2 Release Tag**: `a2-final`
- **Gold Test Set SHA-256**: `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`
- **Train Split SHA-256**: `f75a7a0779ca54fcd532904aa17586d24b1c6f876549bf70f89bc2e929cc3122`
- **Val Split SHA-256**: `b544e5aa091b093f9ca469b69e0fcca7170ba1fd233270567f742406a2f21dfa`
- **Test Split SHA-256**: `be9b04ed9b40e1f99265d1a36f0cb9b5671837dae27882f41aeb2b72403dd971`
- **Cohort B Shifted SHA-256**: `0d780ed6b5e4456590bdaa115f1815594d185b1e6372fb607c6afd78f285a47f`
- **Assignment 1 Report**: [report/report.pdf](report/report.pdf)
- **Assignment 2 Report**: [report/report2.pdf](report/report2.pdf)
- **Assignment 2 Interactive Dashboard**: [report/index2.html](report/index2.html)
