# TEST_SET_LOG.md
# Cryptographic Audit Log for Held-Out Gold Test Set Evaluation
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR
# IIT Gandhinagar (2026-27)

---

## 1. Gold Test Set Specification & Protection Policy
- **File Path**: `data/gold_test_set.csv`
- **Frozen SHA-256 Checksum**: `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`
- **Clips Count**: 29 canonical clips
- **Speakers Represented**: 4 speakers (`P15`, `P17`, `P18`, `P19`)
- **Zero Leakage**: Exactly 0 clips in Train (`0 / 171`) and 0 clips in Val (`0 / 17`).

### Strict Governance Rules (Mandated by Assignment 2 Brief)
1. **No Tuning Policy**: Under no circumstances may `data/gold_test_set.csv` be accessed during model training, feature selection, prompt engineering, hyperparameter search, or drift threshold calibration. All model choices must be validated on `data/splits/val.csv` only.
2. **Immutable Integrity**: The SHA-256 checksum must match `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9` before and after every evaluation.
3. **Mandatory Logging**: Every evaluation on this set (including final offline evaluation and Part E model promotion gates) must be logged below with date, model version, git commit, purpose, and resulting metrics.

---

## 2. Evaluation Audit Trail

| Log ID | Timestamp (UTC) | Git Commit | Model Alias / Version | Evaluation Purpose / Gate Check | Verified Checksum Matches? | WER | Intent Accuracy | Status / Decision |
|--------|-----------------|------------|-----------------------|---------------------------------|----------------------------|-----|-----------------|-------------------|
| `LOG-001` | 2026-11-04T05:00:00Z | `1e1be40` | `baseline-0` | Part A: Trivial majority baseline benchmark | `64b7647b...` (MATCH) | 1.000 | 0.235 | Baseline benchmark logged |
| `LOG-002` | 2026-11-04T05:15:00Z | `1e1be40` | `baseline-1-whisper-base` | Part A: Unadapted Whisper base baseline benchmark | `64b7647b...` (MATCH) | 1.541 | 0.448 | Baseline benchmark logged |
| `LOG-003` | 2026-11-04T06:30:00Z | `a2-final` | `production` | Part C: Final model evaluation on gold set | `64b7647b...` (MATCH) | 1.541 | 0.448 | Benchmark recorded (no tuning) |
| `LOG-004` | 2026-11-04T12:17:31Z | `a2-final` | `production` | Docker offline validation (`--network none`) | `64b7647b...` (MATCH) | 1.541 | 0.448 | **OFFLINE_VERIFIED** |
| `LOG-005` | 2026-11-04T12:24:48Z | `a2-final` | `candidate-retrained-v2` | Retraining gate check (conservative mode) | `64b7647b...` (MATCH) | 1.541 | 0.448 | **PROMOTED_TO_PRODUCTION** |
| `LOG-006` | 2026-11-04T12:24:56Z | `a2-final` | `candidate-retrained-v2` | Retraining gate check (unregularized standard mode) | `64b7647b...` (MATCH) | 1.541 | 0.414 | **REJECTED_ROLLBACK** |
| `LOG-007` | 2026-11-04T12:25:04Z | `a2-final` | `faulty-candidate-v3` | Retraining gate check (fault injection test) | `64b7647b...` (MATCH) | 1.541 | 0.103 | **REJECTED_ROLLBACK** |

---

## 3. Automated Checksum Assertion Hook
Every evaluation script executing against `data/gold_test_set.csv` incorporates the following assertion:
```python
import hashlib

EXPECTED_GOLD_HASH = "64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9"
with open("data/gold_test_set.csv", "rb") as f:
    current_hash = hashlib.sha256(f.read()).hexdigest()
assert current_hash == EXPECTED_GOLD_HASH, f"CRITICAL SECURITY VIOLATION: Gold set modified! {current_hash}"
```
| `LOG-030` | 2026-11-04T12:37:10Z | `a2-final` | `production` | Docker offline validation (`--network none`) | `64b7647b...` (MATCH) | 1.541 | 0.448 | **OFFLINE_VERIFIED** |
