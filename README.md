# Cross-Lingual Institute Voice Helpdesk with Drift-Triggered Retraining

**CS203: Software Tools and Techniques in AI — Assignments 1 & 2 (Project 5)**  
Department of Computer Science and Engineering, Indian Institute of Technology Gandhinagar  
**Repository**: [https://github.com/vipulSP2108/STTAI_Project.git](https://github.com/vipulSP2108/STTAI_Project.git)

**Current Docker path** — The revised 182-clip corpus is the working dataset. See [Docker build and verification](DOCKER.md) and the [checkpoint plan](ASSIGNMENT_CHECKPOINT_PLAN.md). The pilot metrics, experiment commands and tags below describe historical work.

---

## Team & Equal Contribution Statement

| Team Member | Roll Number | Academic Program | Role & Contribution |
| :--- | :--- | :--- | :--- |
| **Rajdeep Vraj** | 24110260 | B.Tech CSE and AI, IIT Gandhinagar | 33.3% Equal Technical Contribution |
| **Vipul Sunil Patil** | 24110381 | B.Tech CSE and CE, IIT Gandhinagar | 33.3% Equal Technical Contribution |
| **Satvik Sharma** | 24110300 | B.Tech CSE, IIT Gandhinagar | 33.3% Equal Technical Contribution |

> **Statement of Equal Contribution (1/3rd each across Assignments 1 & 2):**  
> All three team members (**Rajdeep Vraj**, **Vipul Sunil Patil**, and **Satvik Sharma**) contributed equally (33.3% each) across all phases of this project:
> - **Assignment 1 (Data Engineering & Governance):** Authentic audio corpus collection (19 student speakers, 5 acoustic environments, 249 clips), 14-check validation suite with 12-case corruption tests, Label Studio double annotation with guideline iteration ($\kappa=0.7228 \to 0.8446$), multi-condition acoustic augmentations, 5-fold active learning simulation, speaker-disjoint splits, and research report 1 (`report/report.pdf`, tag `a1-final`).
> - **Assignment 2 (Modeling, Deployment, Monitoring & Governance):** Baseline formulating (Trivial Majority, Unadapted Whisper + TF-IDF) and proposed adapted Whisper routing head, 15-run MLflow experiment tracking (`supporting_files/mlflow.db`) with Pareto frontier analysis, 1,000 bootstrap CI evaluations, Wilcoxon signed-rank and McNemar paired significance testing, slice analysis, 20 categorized test error modes, self-contained offline Docker image for `linux/amd64` ($\le 4.2$ GB RAM, `--network none` verified), FastAPI REST service, interactive Streamlit UI, 5-batch traffic drift simulation ($r=0.41$, Batch 5 alert), closed-loop active retraining with rigid 2-stage promotion gating, and research report 2 (`report/report2.pdf`, tag `a2-final`).

---

## Participant Privacy & Data Provenance Protocol

In adherence to ethical human research standards and institutional participant privacy preferences at IIT Gandhinagar:
- **Anonymized Numerical Identifiers**: Participants requested that their personal names and roll numbers remain confidential. Accordingly, all metadata manifests, collection logs, and split files index speakers using standardized tokens: **P1 through P19**. Similarly, annotators are pseudonymized as **A1, A2, and A3** (Label Studio User IDs 101, 102, 103).
- **Spoken Audio Collection**: Audio clips were captured from student participants across 19 smartphone models in 5 campus environments (hostel rooms, mess dining halls, academic corridors, campus libraries, outdoor canteens). Total duration is 1.25 hours (4,516.5 s, under 2.0 h target; disclosed transparently).
- **Transparent Disclosure on Reference Transcripts & Keyword Leakage**:
  - In Assignment 1, reference transcripts were prepared using institutional helpdesk query templates structured around four core domains (Admissions, Hostel/Mess, IT Support, Student Services).
  - An empirical keyword leakage audit (`code/check_keyword_leak.py`) demonstrates that a linear classifier trained on solely the *first 3 words* of these reference transcripts achieves **100% intent classification accuracy**, confirming that the reference text contains formulaic introductory phrases.
  - In contrast, when the system evaluates unconstrained student speech transcribed by Whisper ASR, intent accuracy drops to **23.98%** on uncorrected gold and **30.76%** on corrected gold, reflecting real-world conversational ambiguity and cross-lingual phonetic transliteration divergence.

---

## Assignment 2: Model Development, Deployment & Monitoring

### Key Results Summary

| Metric / Stage | Baseline 0 (Trivial) | Baseline 1 (Zero-Shot) | Proposed (`production`) | Retrained (`candidate-retrained-v2`) |
| :--- | :--- | :--- | :--- | :--- |
| **Gold Test Set WER** | 1.000 | 1.2719 [1.1557, 1.3933] | **1.2719 [1.1557, 1.3933]** | 1.2719 [1.1557, 1.3933] |
| **Gold Test Set CER** | 1.000 | 0.9447 [0.8910, 1.0064] | **0.9447 [0.8910, 1.0064]** | 0.9447 [0.8910, 1.0064] |
| **Gold Intent Accuracy (ASR)** | 23.5% | 31.00% [13.79%, 48.28%] | **24.14% [10.26%, 41.38%]** | **24.14%** (Passes strict ex-ante $\le 2.0\%$ gate with 0.0% degradation) |
| **Corrected Gold Intent Acc** | 23.5% | 41.54% [24.14%, 58.62%] | **30.76% [13.79%, 48.28%]** | **30.76%** |
| **Reference Text Intent Acc** | 23.5% | 41.38% (Template Leak) | **41.38% (Template Leak)** | **41.38%** |
| **Gold Intent Macro-F1** | 0.095 | 0.2850 [0.1200, 0.4400] | **0.2245 [0.0833, 0.3886]** | **0.2050** |
| **Cohort B Held-Out (P13) Acc**| 23.1% | 25.22% [12.50%, 40.62%] | 30.77% [7.69%, 53.85%] | **38.46%** ($+7.7\%$ gain $\ge +5\%$) |
| **CPU Routing Latency** | < 0.01 ms | 0.007 ms | **0.007 ms** | **0.007 ms** |
| **Total Inference Latency (p50)**| — | 2,855.2 ms | **2,855.2 ms** (RTF: 0.165) | **2,855.2 ms** |
| **Peak Memory Footprint** | — | — | **782.73 MB** (Darwin arm64) | **782.73 MB** |
| **Statistical Significance** | — | — | Wilcoxon $W=0.0, p=1.0000$* | McNemar $\chi^2=0.10, p=0.7518$ |

*\*Note on Significance: Wilcoxon p=1.0000 and McNemar p=0.7518 evaluate paired differences against Baseline 1 on the identical 29 gold clips, confirming no statistically significant difference.*

### Cryptographic Gold Test Set Integrity
The held-out Gold Test Set (`data/gold_test_set.csv`) was created during Assignment 1 and remains **100% immutable** across Assignment 2:
- **Immutable SHA-256 Checksum**: `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`
- **Zero Training / Tuning Leakage**: Gold clips were never used for training or hyperparameter selection.
- **Audit Log**: Every evaluation is logged in [`TEST_SET_LOG.md`](TEST_SET_LOG.md) with exact timestamp, caller, model version, and SHA-256 assertions.

---

## Assignment 2 Quickstart (Standard 5 Reproduction Commands)

```bash
# 1. Checkout submission release tag
git checkout a2-final

# 2. Install pinned dependencies (==)
pip install -r code/requirements.txt

# 3. Pull versioned data artifacts via DVC
dvc pull

# 4. Speaker-disjoint evaluation: CV ablation, then the release split (selection on validation, test once)
python model/src/training/intent_v2.py --ablation --sources asr_hybrid --only B0,B7 --tag soft
python model/src/evaluation/release_eval.py

# 5. Bias, reference and language-routing audits
python model/src/evaluation/bias_audit.py && python model/src/asr/reference_audit.py && python model/src/asr/lid_router.py
```

### Additional pipeline commands (indic-v2)
```bash
# Decoder confidence for all clips (active learning + monitoring input)
python model/src/asr/decode_confidence.py
# Active learning: decoder confidence vs random (A1 Part D)
python model/src/training/active_learning_confidence.py
# Audio augmentation robustness on the final corpus
python model/src/augmentation/audio_robustness.py
# Drift replay -> alert -> AL selection -> retrain -> frozen gate (A2 Part E)
python code/a2_part_e_monitoring/release_drift_loop.py
# Docker build / offline validation / UI: see docs/DOCKER_FRIEND_RUNBOOK.md and DOCKER.md
# Pilot-era scripts (validate_offline.py, traffic_replay.py, retrain_pipeline.py) are historical only.
```

---

## Docker Deployment & Offline Verification

Follow [DOCKER.md](DOCKER.md) to stage the revised WAVs outside Git, build the `linux/amd64` image, validate the 40-clip revised test split with `--network none`, and start Streamlit and FastAPI. The CI `runtime` target uses a synthetic WAV for its prediction test. The original frozen gold remains a separate benchmark.

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

## Team Contributions & Development Environment

All pipeline modules, experimental runs, and Docker containerizations were implemented collaboratively through in-person pair-programming sessions conducted on a shared primary development workstation (macOS / Docker host). While Git commits originate from this joint workstation environment, functional domain ownership was strictly divided among all three team members with equal 33.3% contributions:

| Member | Roll Number | Primary Functional Responsibilities |
| :--- | :--- | :--- |
| **Rajdeep Vraj** | `24110260` | Audio collection protocol, 14-check validation suite, VAD normalization, Docker containerization (`code/Dockerfile`), and offline image verification. |
| **Vipul Sunil Patil** | `24110381` | Label Studio dual annotation, TF-IDF + MLP intent routing, 15-run MLflow & W&B experiment tracking, FastAPI service, and Streamlit UI. |
| **Satvik Sharma** | `24110300` | Statistical evaluation, Wilson score & 1,000 bootstrap CIs, slice analysis, traffic replay drift detection, and automated retraining gates. |

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
