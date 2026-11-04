# CS203 Assignment 1 — Project 5: Voice Helpdesk ASR
**Cross-Lingual Institute Voice Helpdesk with Drift-Triggered Retraining**

- **Team**: Rajdeep Vraj, Vipul Sunil Patil, Satvik Sharma
- **Equal Contribution**: All 3 members contributed equally (33.3% each) to all project phases.
- **Course**: CS 203, IIT Gandhinagar, Semester I 2026-27
- **GitHub**: https://github.com/vipulSP2108/STTAI_Project.git
- **Participant Anonymization**: Per participant and evaluator privacy preferences, numerical tokens (P1–P19 for speakers, A1–A3 for annotators) are used in all public manifests while preserving 100% authentic campus recordings and acoustics.
- **Deadline**: 18 October 2026 (Release Tag: `a1-final`)

---

## Quickstart — Rebuild Pipeline in 5 Commands

```bash
# 1. Install all dependencies strictly pinned with ==
pip install -r requirements.txt

# 2. Build metadata.csv from raw audio files
python part_a_collection/build_metadata.py --audio-dir ../data/raw/audio/

# 3. Run 14 validation checks (all pass on clean calibrated data)
pytest part_b_validation/validation_suite.py -v

# 4. Compute inter-annotator agreement + freeze gold test set
python part_c_labelling/compute_agreement.py

# 5. Create leakage-free speaker-disjoint splits (train/val/test/cohort_b)
python part_e_versioning/make_splits.py
```

---

## What Each Command Does

| Step | Command | Output Artifact |
|------|---------|-----------------|
| 1 | `pip install -r requirements.txt` | Python environment pinned to exact versions (`==`) |
| 2 | `build_metadata.py` | `data/metadata.csv` with SHA-256 hashes & provenance |
| 3 | `pytest validation_suite.py -v` | 14 quality checks on audio, text, Pandera schema, and leakage |
| 4 | `compute_agreement.py` | Agreement report (WER & $\kappa$), freezes `data/gold_test_set.csv` (29 clips) |
| 5 | `make_splits.py` | Speaker-disjoint `data/splits/*.csv` (Train: 171, Val: 17, Test: 29, Cohort B: 32) |

---

## Data Lifecycle Architecture

```
Speaker recording (P1-P19) → ingest_records.py → data/raw/audio/*.wav (249 clips)
                                                → data/metadata.csv (19 phones, 5 noises)
                                                ↓
                                    validation_suite.py (14 checks, 100% pass)
                                                ↓
                               Label Studio (Level 1: transcripts, Level 2: intent)
                                                ↓
                                compute_agreement.py → agreement_report.json
                                                     → data/gold_test_set.csv (29 held-out test clips)
                                                ↓
                                 augment_audio.py → data/processed/augmented/ (60 clips)
                                                  → augmentation_wer_table.csv (Whisper WER)
                               active_learning.py → supporting_files/plots/ (5-fold AL curve)
                                                ↓
                                  make_splits.py → data/splits/ (Train: 171, Val: 17, Test: 29, Cohort B: 32)
                                                ↓
                                     git tag a1-final (Release freeze)
```

---

## Checksum Handoff Summary for Assignment 2
- `data/gold_test_set.csv`: `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`
- `data/splits/train.csv`: `f75a7a0779ca54fcd532904aa17586d24b1c6f876549bf70f89bc2e929cc3122`
- `data/splits/val.csv`: `b544e5aa091b093f9ca469b69e0fcca7170ba1fd233270567f742406a2f21dfa`
- `data/splits/test.csv`: `be9b04ed9b40e1f99265d1a36f0cb9b5671837dae27882f41aeb2b72403dd971`
- `data/splits/cohort_b_shifted.csv`: `0d780ed6b5e4456590bdaa115f1815594d185b1e6372fb607c6afd78f285a47f`
