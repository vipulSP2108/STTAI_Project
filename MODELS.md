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
| **`production`** | `artefacts/models/production_v1_head.pt`<br>`artefacts/models/proposed_vectorizer.pkl` | `eaeb1a968806366792f23df4885cb98df0eb696a093007d12e46de35bfd9ddba`<br>`9c88b5a597035d5e289c5a0e8069f9426cd9d0396313b1bde0bc66d297425070` | Prompt-Conditioned Whisper Base + Sublinear TF-IDF + 2-layer MLP (64 hidden, ReLU, Dropout 0.2) | 254 KB<br>44 KB | Primary production model selected from 15 MLflow runs |
| **`candidate-retrained-v2`** | `artefacts/models/candidate_retrained_v2.pt`<br>`artefacts/models/candidate_retrained_vectorizer.pkl` | `a7decd5ea05db2c9be36a152de48a033f2d893f89e174c3a276577ce7edbec59`<br>`7ce41e55b652a45218412a64a817116b365c43a003f7a0e98fa22e1eefdbe81a` | Active-learning retrained classifier adapted to Cohort B regional acoustic shift | 254 KB<br>43 KB | Retrained model evaluated against held-out Gold test set gate |

---

## 2. Checksum Verification Script

To cryptographically verify all model checkpoints locally:
```python
import hashlib
from pathlib import Path

EXPECTED_HASHES = {
    "artefacts/models/baseline1.pkl": "0991d01e469041e7b8c6ad82eb7c361de52be3f7ae6cb117a366978cc7493233",
    "artefacts/models/production_v1_head.pt": "eaeb1a968806366792f23df4885cb98df0eb696a093007d12e46de35bfd9ddba",
    "artefacts/models/proposed_vectorizer.pkl": "9c88b5a597035d5e289c5a0e8069f9426cd9d0396313b1bde0bc66d297425070",
    "artefacts/models/candidate_retrained_v2.pt": "a7decd5ea05db2c9be36a152de48a033f2d893f89e174c3a276577ce7edbec59",
    "artefacts/models/candidate_retrained_vectorizer.pkl": "7ce41e55b652a45218412a64a817116b365c43a003f7a0e98fa22e1eefdbe81a"
}

for path_str, exp_hash in EXPECTED_HASHES.items():
    p = Path(path_str)
    assert p.exists(), f"Missing file: {path_str}"
    with open(p, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    assert digest == exp_hash, f"Hash mismatch for {path_str}: got {digest}, expected {exp_hash}"
    print(f"✓ Verified: {path_str} matches expected SHA-256")
```
