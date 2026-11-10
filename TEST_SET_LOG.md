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
| `LOG-002` | 2026-11-04T05:15:00Z | `1e1be40` | `baseline-1-whisper-base` | Part A: Unadapted Whisper base baseline benchmark | `64b7647b...` (MATCH) | 1.279 | 0.346 | Baseline benchmark logged |
| `LOG-003` | 2026-11-05T03:02:52Z | `5b41413` | `production` | Part C: Full offline evaluation suite on gold set | `64b7647b...` (MATCH) | 1.279 | 0.346 | **EVALUATED** |
| `LOG-004` | 2026-11-05T08:35:04Z | `a2-final` | `production` | Part D: Isolated offline validation (`validate_offline.py`) | `64b7647b...` (MATCH) | 1.277 | 0.345 | **OFFLINE_VERIFIED** |
| `LOG-005` | 2026-11-05T13:08:12Z | `a8b2348` | `candidate-retrained-v2` | Part E: Active Retraining Gate (mode: rehearsal) | `64b7647b...` (MATCH) | 1.277 | 0.310 | **PROMOTED_TO_PRODUCTION** |
| `LOG-006` | 2026-11-05T13:08:21Z | `a8b2348` | `candidate-no-rehearsal-v1` | Part E: Active Retraining Gate (mode: no_rehearsal) | `64b7647b...` (MATCH) | 1.277 | 0.345 | **REJECTED_ROLLBACK** |
| `LOG-418` | 2026-11-06T04:46:58Z | `17ace7b` | `candidate-retrained-v2` | Active Retraining Gate (rehearsal) | `64b7647b...` (MATCH) | 1.270 | 0.310 | **REJECTED_ROLLBACK** |
| `LOG-179` | 2026-11-06T04:59:39Z | `17ace7b` | `candidate-retrained-v2` | Active Retraining Gate (rehearsal) | `64b7647b...` (MATCH) | 1.358 | 0.207 | **PROMOTED_TO_PRODUCTION** |
| `LOG-188` | 2026-11-06T04:59:48Z | `17ace7b` | `candidate-no-rehearsal-v1` | Active Retraining Gate (no_rehearsal) | `64b7647b...` (MATCH) | 1.358 | 0.241 | **REJECTED_ROLLBACK** |

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
| `LOG-853` | 2026-11-06T01:34:13Z | `17ace7b4` | `production` | Automated evaluation suite | `64b7647b...` (MATCH) | 1.272 | 0.346 | **EVALUATED** |
| `LOG-327` | 2026-11-06T04:28:47Z | `17ace7b4` | `production` | Automated evaluation suite | `64b7647b...` (MATCH) | 1.272 | 0.240 | **EVALUATED** |
| `LOG-948` | 2026-11-06T04:39:08Z | `17ace7b4` | `production` | Automated evaluation suite | `64b7647b...` (MATCH) | 1.272 | 0.240 | **EVALUATED** |
| `LOG-016` | 2026-11-08T06:20:16Z | `a2-final` | `production` | Docker offline validation (`--network none`) | `64b7647b...` (MATCH) | 1.358 | 0.241 | **OFFLINE_VERIFIED** |
| `LOG-016` | 2026-11-08T06:20:16Z | `a2-final` | `production` | Docker offline validation (`--network none`) | `64b7647b...` (MATCH) | 1.358 | 0.241 | **OFFLINE_VERIFIED** |
