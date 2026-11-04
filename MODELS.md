# MODELS.md
# Model Checkpoints, Registry Aliases & Checksum Verification
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR

---

## 1. Registered Models & Checkpoints

All models operate locally on CPU (PyTorch FP32 baseline) without external API dependencies.

| Model Stage / Alias | Checkpoint File | Checksum (SHA-256) | Architecture & Components | Size | Primary Evaluation Purpose |
|---------------------|-----------------|--------------------|---------------------------|------|----------------------------|
| **`baseline-0`** | `artefacts/models/baseline0.pkl` | `7d10e53a...` | Majority Class Intent Classifier + Dummy ASR | 12 KB | Trivial unadapted lower bound |
| **`baseline-1`** | `artefacts/models/baseline1_whisper_tiny.pt` | `bd577a11...` | Unadapted OpenAI Whisper Tiny + TF-IDF Classifier | 75 MB | Assignment 1 zero-shot baseline |
| **`production-v1`** | `artefacts/models/production_v1.pt` | `a3f9104c...` | Adapted Whisper Encoder + Joint Linear Intent Routing Head | 76 MB | Selected candidate model from 15 tuning runs |
| **`candidate-retrained-v2`** | `artefacts/models/candidate_v2.pt` | `c8e119b5...` | Active-learning retrained model on Cohort B drift queries | 76 MB | Retrained model promoted via gate check |

---

## 2. Checksum Verification
```python
import hashlib

def verify_model(path, expected_hash):
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    assert digest == expected_hash, f"Hash mismatch for {path}: {digest}"
    print(f"Verified: {path}")
```
