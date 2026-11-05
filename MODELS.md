# MODELS.md
# Model Checkpoints, Registry Aliases & Checksum Verification
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR

---

## 1. Registered Models & Checkpoints

All models operate locally on CPU (PyTorch FP32 baseline) without external API dependencies.
The ASR backbone uses off-the-shelf OpenAI Whisper `base` (71.8M parameters, FP32 CPU execution) and adapted cross-attention checkpoint `whisper_base_adapted.pt` (6.3M cross-attention parameters adapted with encoder frozen). Domain intent routing heads and TF-IDF feature extractors are trained and stored locally in `artefacts/models/`.

| Model Stage / Alias | Checkpoint File | Checksum (SHA-256) | Architecture & Components | Size | Primary Evaluation Purpose |
|---------------------|-----------------|--------------------|---------------------------|------|----------------------------|
| **`baseline-0`** | *(algorithmic)* | N/A | Trivial Majority Class Intent Classifier (`admissions`) | < 1 KB | Unadapted empirical lower bound |
| **`baseline-1`** | `artefacts/models/baseline1.pkl` | `0991d01e469041e7b8c6ad82eb7c361de52be3f7ae6cb117a366978cc7493233` | Off-the-shelf Whisper Base + TF-IDF (1,000) Logistic Regression | 72.8 KB | Assignment 1 zero-shot baseline |
| **`whisper-adapted`** | `artefacts/models/whisper_base_adapted.pt` | `628f8fb4dee9168d5feef7bec44b71ae1e349ab7f4129bd1ed32f5a5f323730c` | Whisper Base Decoder Cross-Attention Fine-Tuned (`freeze_encoder: true`, 6.3M params) | 25.2 MB | Acoustic adaptation for Gujarati-English bilingual speech |
| **`production`** | `artefacts/models/production_v1_head.pt`<br>`artefacts/models/proposed_vectorizer.pkl` | `b4a507ad3d8a9b42de15190d6dcafa7c16104231fa0d69c201b17bc8768a4cce`<br>`bdfe4bf0b21fa92d7067c9db32c5b9854e32aa095e22aac18f8a97b7b24afa5f` | Whisper Base + Normalized TF-IDF (1,000) + 2-layer MLP (64 hidden, ReLU, Dropout 0.2) | 260 KB<br>40.1 KB | Primary production model selected from 41 MLflow runs |
| **`candidate-retrained-v2`** | `artefacts/models/candidate_retrained_v2.pt`<br>`artefacts/models/candidate_retrained_vectorizer.pkl` | `b6179ed59c4747ee5b67f37b4b73649890239fd4ae2b348e68010e15b3b9955d`<br>`a2ec88f5606be12eaa422a4e1f024853f052d761df6e5c50e7cadd206199d172` | Active-learning retrained classifier adapted to Cohort B regional acoustic shift (Speaker P4 pool) | 260 KB<br>40 KB | Retrained candidate evaluated against held-out Gold test set gate |

---

## 2. Checksum Verification Script

To cryptographically verify all model checkpoints locally:
```python
import hashlib
from pathlib import Path

EXPECTED_HASHES = {
    "artefacts/models/baseline1.pkl": "0991d01e469041e7b8c6ad82eb7c361de52be3f7ae6cb117a366978cc7493233",
    "artefacts/models/whisper_base_adapted.pt": "628f8fb4dee9168d5feef7bec44b71ae1e349ab7f4129bd1ed32f5a5f323730c",
    "artefacts/models/production_v1_head.pt": "b4a507ad3d8a9b42de15190d6dcafa7c16104231fa0d69c201b17bc8768a4cce",
    "artefacts/models/proposed_vectorizer.pkl": "bdfe4bf0b21fa92d7067c9db32c5b9854e32aa095e22aac18f8a97b7b24afa5f",
    "artefacts/models/candidate_retrained_v2.pt": "b6179ed59c4747ee5b67f37b4b73649890239fd4ae2b348e68010e15b3b9955d",
    "artefacts/models/candidate_retrained_vectorizer.pkl": "a2ec88f5606be12eaa422a4e1f024853f052d761df6e5c50e7cadd206199d172"
}

for path_str, exp_hash in EXPECTED_HASHES.items():
    p = Path(path_str)
    assert p.exists(), f"Missing file: {path_str}"
    with open(p, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    assert digest == exp_hash, f"Hash mismatch for {path_str}: got {digest}, expected {exp_hash}"
    print(f"✓ Verified: {path_str} matches expected SHA-256")
```
