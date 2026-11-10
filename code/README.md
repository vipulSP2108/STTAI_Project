# CS203 Assignments 1 & 2 — Project 5: Voice Helpdesk ASR
**Cross-Lingual Institute Voice Helpdesk with Drift-Triggered Retraining**

- **Team**: Rajdeep Vraj, Vipul Sunil Patil, Satvik Sharma
- **Equal Contribution**: All 3 members contributed equally (33.3% each) across all project phases in both Assignment 1 and Assignment 2.
- **Course**: CS 203, IIT Gandhinagar, Semester I 2026-27
- **GitHub**: https://github.com/vipulSP2108/STTAI_Project.git
- **Participant Anonymization**: Per participant and evaluator privacy preferences, numerical tokens (P1–P19 for speakers, A1–A3 for annotators) are used in all public manifests while preserving 100% authentic campus recordings and acoustics.
- **Release Tags**: `a1-final` (Assignment 1), `a2-final` (Assignment 2)

---

## Assignment 2 Quickstart (5 Reproduction Commands)

```bash
# 1. Install pinned dependencies (==)
pip install -r requirements.txt

# 2. Run 15-run MLflow hyperparameter tuning search
python a2_part_b_tuning/tune_experiments.py

# 3. Evaluate unified production model on held-out gold test set with 1,000 bootstrap CIs
python a2_part_c_evaluation/evaluate.py --split gold

# 4. Replay production traffic and verify drift detection (Batch 3 alert)
python a2_part_e_monitoring/traffic_replay.py

# 5. Execute closed-loop active retraining and promotion
python a2_part_e_monitoring/retrain_pipeline.py
```

---

## Assignment 2 Modules & Artefacts

| Module | Purpose | Key Artifacts |
| :--- | :--- | :--- |
| `a2_part_a_models/` | Baseline 0 (majority), Baseline 1 (unadapted Whisper + TF-IDF), Proposed adapted router | `supporting_files/part_a_baselines_benchmark.json`, `artefacts/models/` |
| `a2_part_b_tuning/` | 15-run systematic hyperparameter search logged to local SQLite MLflow | `supporting_files/mlflow.db`, `supporting_files/plots/tuning_runs.json`, `supporting_files/plots/tuning_search_analysis.png` |
| `a2_part_c_evaluation/` | Unified evaluation CLI with 1,000 bootstrap CIs, slice analysis, 20 categorized errors | `supporting_files/error_analysis.csv`, `MODEL_CARD.md` |
| `a2_part_d_deployment/` | Revised CPU release, offline validator, FastAPI service and Streamlit UI | `Dockerfile`, `supporting_files/revised_validation.json`, `DOCKER.md` |
| `a2_part_e_monitoring/` | 5-batch traffic replay, label-free entropy tracking ($r=0.91$), gated retraining | `data/replay/traffic_stream.jsonl`, `data/retraining/`, `TEST_SET_LOG.md` |
| `scripts/` | Automated ReportLab PDF generator mirroring `report/report2.tex` | `report/report2.pdf` (7 pages) |

---

## Docker Offline Verification & UI Launch

The current instructions are in [DOCKER.md](../DOCKER.md). The revised release uses external DVC staging and a separate speaker-disjoint test split. The other experiment commands in this document are for the historical pilot.

---

## Assignment 1 Checksum Handoff Summary
- `data/gold_test_set.csv`: `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9` (strictly immutable)
- `data/splits/train.csv`: `f75a7a0779ca54fcd532904aa17586d24b1c6f876549bf70f89bc2e929cc3122`
- `data/splits/val.csv`: `b544e5aa091b093f9ca469b69e0fcca7170ba1fd233270567f742406a2f21dfa`
- `data/splits/test.csv`: `be9b04ed9b40e1f99265d1a36f0cb9b5671837dae27882f41aeb2b72403dd971`
- `data/splits/cohort_b_shifted.csv`: `0d780ed6b5e4456590bdaa115f1815594d185b1e6372fb607c6afd78f285a47f`
