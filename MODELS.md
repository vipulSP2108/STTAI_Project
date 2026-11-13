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
| **`whisper-adapted`** | `artefacts/models/whisper_base_adapted.pt` | `c80b27f11046915028cb1633f22a615f636b38d0eb9266bd77300ec481cf06f0` | Whisper Base Decoder Cross-Attention Fine-Tuned (`freeze_encoder: true`, 6.3M params) | 25.2 MB | Acoustic adaptation for Gujarati-English bilingual speech |
| **`production`** | `artefacts/models/production_v1_head.pt`<br>`artefacts/models/proposed_vectorizer.pkl` | `a88ea47b9fd483836f4f43b281a45f4edfc84b7ae25ba77bfda7bdbe908f1fd3`<br>`9219bc297dbb3a2f7a22899ef15f00db2f544fb060c79a2cb3e6a891e1588e47` | Whisper Base + Normalized TF-IDF (1,000) + 2-layer MLP (64 hidden, ReLU, Dropout 0.2) | 260 KB<br>37.0 KB | Primary production model selected from 15 systematic MLflow runs (Run 6) |
| **`staging`** | `artefacts/models/staging_head.pt`<br>`artefacts/models/staging_vectorizer.pkl` | `3b164b92c10ff553bab0258baffc93b2137dbb1ce0c7a6403956cda9cf2df118`<br>`9625e8b421929121a6ccbff53bb6d4ffcb5400953d4dda2bac0368d750567377` | Whisper Base + TF-IDF (1,000) + 2-layer MLP (128 hidden, ReLU, Dropout 0.2) | 218 KB<br>15.3 KB | Staging candidate registered in MLflow (Run 9) |
| **`candidate-retrained-v2`** | `artefacts/models/candidate_retrained_v2.pt`<br>`artefacts/models/candidate_retrained_vectorizer.pkl` | `f3b7fe55734b33ecc937c76e0ef08e19367e979fb75ae9f75111fcf95cffae2f`<br>`493bc4f3c5f3e3df7a038dc678d696d86daf2cb3ca4bd77c26f3e50bdd590ccc` | Active-learning retrained classifier adapted to Cohort B regional acoustic shift (Speaker P4 pool) | 260 KB<br>39.9 KB | Retrained candidate evaluated against held-out Gold test set gate |
| **`active-serving-pointer`** | `artefacts/models/serving_pointer.json` | `4fa236e37eeab849712a65f026e00905078d5a2d15a32987971c8a01439581cd` | JSON manifest tracking active production model checkpoint and promotion audit | 679 B | Dynamic serving pointer for FastAPI (`app.py`) and Streamlit (`ui.py`) |

---

## 2. Checksum Verification Script

To cryptographically verify all model checkpoints locally:
```python
import hashlib
from pathlib import Path

EXPECTED_HASHES = {
    "artefacts/models/baseline1.pkl": "0991d01e469041e7b8c6ad82eb7c361de52be3f7ae6cb117a366978cc7493233",
    "artefacts/models/whisper_base_adapted.pt": "c80b27f11046915028cb1633f22a615f636b38d0eb9266bd77300ec481cf06f0",
    "artefacts/models/production_v1_head.pt": "a88ea47b9fd483836f4f43b281a45f4edfc84b7ae25ba77bfda7bdbe908f1fd3",
    "artefacts/models/proposed_vectorizer.pkl": "9219bc297dbb3a2f7a22899ef15f00db2f544fb060c79a2cb3e6a891e1588e47",
    "artefacts/models/staging_head.pt": "3b164b92c10ff553bab0258baffc93b2137dbb1ce0c7a6403956cda9cf2df118",
    "artefacts/models/staging_vectorizer.pkl": "9625e8b421929121a6ccbff53bb6d4ffcb5400953d4dda2bac0368d750567377",
    "artefacts/models/candidate_retrained_v2.pt": "f3b7fe55734b33ecc937c76e0ef08e19367e979fb75ae9f75111fcf95cffae2f",
    "artefacts/models/candidate_retrained_vectorizer.pkl": "493bc4f3c5f3e3df7a038dc678d696d86daf2cb3ca4bd77c26f3e50bdd590ccc",
    "artefacts/models/serving_pointer.json": "4fa236e37eeab849712a65f026e00905078d5a2d15a32987971c8a01439581cd"
}

for path_str, exp_hash in EXPECTED_HASHES.items():
    p = Path(path_str)
    assert p.exists(), f"Missing file: {path_str}"
    with open(p, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    assert digest == exp_hash, f"Hash mismatch for {path_str}: got {digest}, expected {exp_hash}"
    print(f"✓ Verified: {path_str} matches expected SHA-256")
```

---

## 3. Dual-Platform Experiment Tracking: MLflow & Weights & Biases (W&B)

In alignment with **CS203: Software Tools and Techniques in AI**, all 15 systematic hyperparameter tuning runs were concurrently tracked and cross-validated across **both industry-standard MLOps platforms**:

1. **MLflow** (`supporting_files/mlflow.db`, exported to `artefacts/mlflow_export/`):
   - Local, embedded, offline-first SQLite tracking server.
   - Powers zero-network container builds and offline reproducible validation (`--network none`).
   - Registers local model version aliases (`production`, `staging`).

2. **Weights & Biases (W&B)** (Project `voice-helpdesk-asr` under IIT Gandhinagar organization):
   - Synchronized via `code/a2_part_b_tuning/sync_wandb.py` using `WANDB_API_KEY`.
   - Cloud dashboard for distributed team collaboration, interactive runs comparison table, and Pareto trade-off visualization.
   - Logs identical hyperparameters (`lr`, `hidden_dim`, `ngram_max`, `dropout`, `epochs`), validation metrics (accuracy, macro-F1, latency), model size, and Git commit hashes.

### Cross-Validation & Concordance:
- **Identical Optimum**: Both MLflow and W&B independently identify **Run 6** as the Pareto-optimal production champion (`val_accuracy: 52.94%`, `macro-f1: 0.4705`, `size: 251.3 KB`, `latency: 0.007 ms`) and **Run 9** as the staging candidate (`val_accuracy: 47.06%`, `macro-f1: 0.3792`).
- **Complementary Tool Roles**: Demonstrates hands-on proficiency with self-hosted embedded tooling (MLflow) for offline container compliance alongside enterprise managed cloud tooling (W&B) for team visibility.
