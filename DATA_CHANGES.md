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
| **Simulated Annotator Pool** | `data/retraining/annotator_pool.csv` | 32 clips | Pre-labelled pool representing ground-truth annotations from simulated human annotator for drift retraining. Revealed only upon active learning uncertainty query. |
| **Retrained Training Manifest** | `data/retraining/train_retrained.csv` | 187 clips | Augmented training partition incorporating 16 newly labelled drift queries selected via active learning uncertainty scoring, with 0 test or gold leakage. |
| **Cohort B Adaptation Split** | `data/retraining/cohort_b_adapt.csv` | 19 clips (Speaker P4) | Disjoint adaptation pool available for simulated annotator query during active retraining. |
| **Cohort B Held-Out Eval Split** | `data/retraining/cohort_b_heldout.csv` | 13 clips (Speaker P13) | Completely held-out evaluation partition for Cohort B distribution drift; strictly isolated from selection and training. |
| **Cohort B Partition Manifest** | `data/retraining/cohort_b_split.csv` | 32 clips (2 speakers) | Full disjoint partition manifest establishing speaker-isolated adaptation vs evaluation roles. |

---

## 3. Disjoint Cohort B Partitioning Audit (2026-11-05)
- **Files Created**: `data/retraining/cohort_b_adapt.csv`, `data/retraining/cohort_b_heldout.csv`, `data/retraining/cohort_b_split.csv`
- **Reason**: To eliminate evaluation leakage during active retraining (per Section 3.5.1 of Guide). Cohort B evaluation is strictly measured on speaker P13 (13 clips), who is never seen during active selection or retraining.
- **Gold Set Integrity**: Completely untouched. SHA-256 remains `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`.
- **DVC Tracking**: Added and indexed under DVC.

All additions are indexed and tracked via DVC and Git.
