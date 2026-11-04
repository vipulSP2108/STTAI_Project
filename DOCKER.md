# DOCKER.md
# Deployment, Offline Execution & Verification Specification
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR

---

## 1. Container Specifications & Hardware Footprint

| Specification | Target Parameter |
|---------------|------------------|
| **Target Architecture** | `linux/amd64` (Multi-platform compatible) |
| **Execution Mode** | CPU only (No CUDA/GPU required) |
| **Peak Memory Requirement** | $\le 4.2$ GB RAM (Well below the 16 GB brief ceiling) |
| **Container Base Image** | `python:3.10-slim` (Pinned Debian 12 baseline) |
| **Self-Contained Bundling** | All model checkpoints, code, gold test set, and Streamlit/FastAPI UI bundled directly in image |
| **Outbound Network Policy** | **Strictly offline** (`--network none` verified; zero outbound HTTP/API requests) |

---

## 2. Docker Image Commands

### A. Build Container Image
```bash
docker build -t voice-helpdesk-asr:a2-final -f code/Dockerfile .
```

### B. Offline Gold Set Validation (`--network none`)
To verify model performance and complete dataset integrity without internet access:
```bash
docker run --rm --network none voice-helpdesk-asr:a2-final validate
```
**Expected Terminal Output:**
```json
{
  "status": "SUCCESS",
  "evaluation_split": "gold_test_set",
  "evaluated_clips": 29,
  "gold_set_sha256": "64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9",
  "gold_checksum_match": true,
  "model_version": "production",
  "git_commit": "a2-final",
  "metrics": {
    "transcript_wer": 1.5411,
    "transcript_cer": 1.2178,
    "intent_accuracy": 0.4483,
    "intent_macro_f1": 0.429,
    "evaluated_clips": 29,
    "mean_inference_latency_ms": 0.0,
    "cpu_real_time_factor": 0.0,
    "total_audio_duration_sec": 523.8
  },
  "offline_verified": true
}
```
*Note*: The validation script verifies the SHA-256 digest of `data/gold_test_set.csv` before running, asserts `--network none` isolation, and writes formatted JSON output to `/app/supporting_files/offline_validation_output.json`.

### C. Launch Interactive Streamlit UI & REST API
```bash
docker run --rm -p 8501:8501 -p 8000:8000 voice-helpdesk-asr:a2-final
```
Open your browser at:
- **Interactive Web UI**: `http://localhost:8501`
- **REST API Endpoints**: `http://localhost:8000/docs`
  - `POST /predict`: Audio file $\to$ `{transcript, intent, confidence, latency_ms}`
  - `GET /health`: Health status, memory, CPU load
  - `GET /version`: Model version and git commit hash

---

## 3. Image Digest & Artifact Integrity

| Artifact | Checksum (SHA-256) | Size |
|----------|--------------------|------|
| `code/Dockerfile` | `e9f2a41bc...` | 2.1 KB |
| `docker_image.tar.gz` (Archive) | Cataloged in `artefacts/` | 1.85 GB |
| Bundled `base.pt` weights | `a3f9104cc...` | 139 MB |
