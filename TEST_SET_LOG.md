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
| `LOG-001` | 2026-11-04T05:00:00Z | `1e1be40` | `baseline-0` | Part A: Trivial majority baseline benchmark | `64b7647b...` (MATCH) | 1.821 | 0.241 | Baseline benchmark logged |
| `LOG-002` | 2026-11-04T05:15:00Z | `1e1be40` | `baseline-1-whisper-tiny` | Part A: Unadapted Whisper tiny baseline benchmark | `64b7647b...` (MATCH) | 1.679 | 0.448 | Baseline benchmark logged |
| `LOG-003` | 2026-11-04T06:30:00Z | `HEAD` | `production-v1` | Part C: Final model evaluation on gold set | `64b7647b...` (MATCH) | 0.628 | 0.897 | Benchmark recorded (no tuning) |
| `LOG-004` | 2026-11-04T07:15:00Z | `HEAD` | `candidate-retrained-v2` | Part E: Retraining gate check (tolerance $\le 2\%$) | `64b7647b...` (MATCH) | 0.631 | 0.897 | **PROMOTED** (Gold preserved: $\Delta = +0.003 \le 0.02$) |

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
| `LOG-403` | 2026-11-04T10:13:23Z | `HEAD` | `candidate-retrained-v2` | Retraining gate check (tolerance $\le 2\%$) | `64b7647b...` (MATCH) | 0.631 | 0.897 | **PROMOTED_TO_PRODUCTION** |
| `LOG-413` | 2026-11-04T10:13:33Z | `HEAD` | `faulty-candidate-v3` | Retraining gate check (tolerance $\le 2\%$) | `64b7647b...` (MATCH) | 0.631 | 0.820 | **REJECTED_ROLLBACK** |
