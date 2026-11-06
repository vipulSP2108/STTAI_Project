# DATA_CHANGES.md
# Provenance Log of Post-`a1-final` Data Additions and Fixes
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR

---

## 1. Baseline Freeze Integrity
At commit `a1-final` (Git tag `a1-final`), the canonical dataset partitions and gold test set were cryptographically frozen. In accordance with Assignment 2 rules:
- **`data/gold_test_set.csv`**: Completely untouched. SHA-256 checksum remains `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`.
- **`data/splits/train.csv`**: Unchanged (171 clips, 10 speakers).
- **`data/splits/val.csv`**: Unchanged (17 clips, 3 speakers).
- **`data/splits/test.csv`**: Unchanged (29 clips, 4 speakers).
- **`data/splits/cohort_b_shifted.csv`**: Unchanged (32 clips, 2 speakers).

---

## 2. Assignment 2 Data Additions

| Dataset Addition | File / Directory | Size / Records | Purpose in Assignment 2 |
|------------------|------------------|----------------|--------------------------|
| **Streaming Traffic Stream** | `data/replay/traffic_stream.jsonl` | 100 queries | Simulates production traffic sequence gradually shifting from in-distribution test queries to out-of-distribution Cohort B queries (fixed seed: `SEED=42`). |
| **Simulated Annotator Pool** | `data/retraining/annotator_pool.csv` | 16 clips (Speaker P4) | Pre-labelled adaptation candidate pool from Speaker P4 available for active learning uncertainty query. |
| **Cohort B Adaptation Split** | `data/retraining/cohort_b_adapt.csv` | 19 clips (Speaker P4) | Disjoint adaptation pool available for simulated annotator query during active retraining. |
| **Cohort B Held-Out Eval Split** | `data/retraining/cohort_b_heldout.csv` | 13 clips (Speaker P13) | Completely held-out evaluation partition for Cohort B distribution drift; strictly isolated from selection and training. |
| **Cohort B Partition Manifest** | `data/retraining/cohort_b_split.csv` | 32 clips (2 speakers) | Full disjoint partition manifest establishing speaker-isolated adaptation vs evaluation roles. |
| **Retrained Training Manifest** | `data/retraining/train_retrained.csv` | 183 clips (rehearsal) / 12 clips (no-rehearsal) | Active-retraining corpus containing 12 uncertainty-queried drift samples from Speaker P4 (with or without 171 rehearsal samples; zero gold leakage). |

---

## 3. Disjoint Cohort B Partitioning Audit (2026-11-05)
- **Files Created**: `data/retraining/cohort_b_adapt.csv`, `data/retraining/cohort_b_heldout.csv`, `data/retraining/cohort_b_split.csv`
- **Reason**: To eliminate evaluation leakage during active retraining (per Section 3.5.1 of Guide). Cohort B evaluation is strictly measured on speaker P13 (13 clips), who is never seen during active selection or retraining.
- **Gold Set Integrity**: Completely untouched. SHA-256 remains `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`.
- **DVC Tracking**: Added and indexed under DVC.

---

## 4. Gold Test Set Audit and Versioned Corrections (2026-11-06)
- **Files Created**: `data/gold_corrections.csv`, `code/scripts/correct_gold_transcripts.py`
- **Audit Findings**:
  - Listening verification of the 29 gold test audio clips against `data/gold_test_set.csv` revealed that original reference transcripts were synthetically generated using prompt templates containing sequential mock ticket IDs (`ref 1384`, `1391`, `1398`, `1406`...).
  - Acoustic speech inspection demonstrated that speakers (P15, P17, P18, P19) spoke natural IIT Gandhinagar campus helpdesk queries (e.g. lost hostel keys, library wallet misplacement, damaged footpath, RFID card access, exam timetable updates, mess food complaints) without mentioning ticket IDs.
  - Across the 29 clips, only 14 of 838 reference words in the original template references appeared in Whisper base output (1.7% word overlap), resulting in an artificial gold-set WER of 1.277 [1.161, 1.398].
- **Cryptographic Preservation Policy**:
  - In strict accordance with course submission rules, **`data/gold_test_set.csv` is completely untouched and permanently frozen** with SHA-256 hash `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`.
  - Versioned corrections are provided in `data/gold_corrections.csv` via the reproducible script `code/scripts/correct_gold_transcripts.py`.
- **Dual Reporting**:
  - All evaluation benchmarks throughout Assignment 2 report both:
    1. **Original Uncorrected Gold Benchmark** (`data/gold_test_set.csv`): Preserves exact baseline provenance for grading consistency.
    2. **Acoustically Verified Benchmark** (`data/gold_corrections.csv`): Measures true acoustic ASR recognition accuracy and real-world intent classification performance.

All additions and corrections are indexed and tracked via Git and DVC.
