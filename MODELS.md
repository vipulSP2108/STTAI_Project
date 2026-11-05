# MODELS.md
# Model Checkpoints, Registry Aliases & Checksum Verification
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR

---

## 1. Registered Models & Checkpoints

All models operate locally on CPU (PyTorch FP32 baseline) without external API dependencies.
The ASR backbone uses off-the-shelf OpenAI Whisper `base` (71.8M parameters, FP32 CPU execution). Domain intent routing heads and TF-IDF feature extractors are trained and stored locally in `artefacts/models/`.

| Model Stage / Alias | Checkpoint File | Checksum (SHA-256) | Architecture & Components | Size | Primary Evaluation Purpose |
|---------------------|-----------------|--------------------|---------------------------|------|----------------------------|
| **`baseline-0`** | *(algorithmic)* | N/A | Trivial Majority Class Intent Classifier (`admissions`) | < 1 KB | Unadapted empirical lower bound |
| **`baseline-1`** | `artefacts/models/baseline1.pkl` | `0991d01e469041e7b8c6ad82eb7c361de52be3f7ae6cb117a366978cc7493233` | Off-the-shelf Whisper Base + TF-IDF (1,000) Logistic Regression | 71 KB | Assignment 1 zero-shot baseline |
| **`production`** | `artefacts/models/production_v1_head.pt`<br>`artefacts/models/proposed_vectorizer.pkl` | `b4a507ad3d8a9b42de15190d6dcafa7c16104231fa0d69c201b17bc8768a4cce`<br>`66709937172f370d283837e165a437c69b1aa5bae717beb057bbb10362f02c04` | Whisper Base + Normalized TF-IDF (1,000) + 2-layer MLP (64 hidden, ReLU, Dropout 0.2) | 258 KB<br>44 KB | Primary production model selected from 39 MLflow runs |
| **`candidate-retrained-v2`** | `artefacts/models/candidate_retrained_v2.pt`<br>`artefacts/models/candidate_retrained_vectorizer.pkl` | `eb145e1dd0a37de5ad19b09e1173ec986b53699b8d9255bc4df57d6317dee1a8`<br>`ef9f9069858b80acff998ec65e123df281bac7eeaa78db2c6277f387c1b85ebf` | Active-learning retrained classifier adapted to Cohort B regional acoustic shift (Speaker P4 pool) | 258 KB<br>44 KB | Retrained candidate evaluated against held-out Gold test set gate |

---

## 2. Checksum Verification Script

To cryptographically verify all model checkpoints locally:
```python
import hashlib
from pathlib import Path

EXPECTED_HASHES = {
    "artefacts/models/baseline1.pkl": "0991d01e469041e7b8c6ad82eb7c361de52be3f7ae6cb117a366978cc7493233",
    "artefacts/models/production_v1_head.pt": "b4a507ad3d8a9b42de15190d6dcafa7c16104231fa0d69c201b17bc8768a4cce",
    "artefacts/models/proposed_vectorizer.pkl": "66709937172f370d283837e165a437c69b1aa5bae717beb057bbb10362f02c04",
    "artefacts/models/candidate_retrained_v2.pt": "eb145e1dd0a37de5ad19b09e1173ec986b53699b8d9255bc4df57d6317dee1a8",
    "artefacts/models/candidate_retrained_vectorizer.pkl": "ef9f9069858b80acff998ec65e123df281bac7eeaa78db2c6277f387c1b85ebf"
}

for path_str, exp_hash in EXPECTED_HASHES.items():
    p = Path(path_str)
    assert p.exists(), f"Missing file: {path_str}"
    with open(p, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    assert digest == exp_hash, f"Hash mismatch for {path_str}: got {digest}, expected {exp_hash}"
    print(f"✓ Verified: {path_str} matches expected SHA-256")
```
```
