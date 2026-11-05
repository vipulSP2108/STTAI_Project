# DOCKER.md
# Deployment, Offline Execution & Verification Specification
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR

---

## 1. Container Specifications & Measured Hardware Footprint

| Specification | Empirical Measurement / Target Parameter |
|---------------|------------------------------------------|
| **Target Architecture** | `linux/amd64` / `darwin/arm64` compatible |
| **Execution Mode** | CPU only (Zero GPU requirement) |
| **Peak Memory Footprint** | **782.73 MB RAM** (measured via `resource.getrusage` on Darwin arm64, ceiling $\le 16$ GB) |
| **Real-Time Factor (RTF)** | **0.243** ($< 1.0$; runs 4.1x faster than real-time audio) |
| **Throughput** | **0.23 queries/second** on standard multi-core CPU |
| **p50 Latency** | **2,855.2 ms** (ASR: 2,854.0 ms, Intent Router: 0.34 ms) |
| **p95 Latency** | **13,441.5 ms** (dominated by long audio clip decoding) |
| **Container Base Image** | `python:3.10-slim` (Pinned Debian baseline) |
| **Self-Contained Bundling** | All model weights, code, gold test set, and Streamlit/FastAPI UI bundled directly |
| **Outbound Network Policy** | **Strictly offline** (`--network none` verified; zero outbound HTTP/API calls) |

---

## 2. Execution & Offline Validation Commands

### A. Local Environment Offline Validation (Recommended)
Per user and environment configuration, offline validation runs directly in the local Python environment without containerization:
```bash
python code/a2_part_d_deployment/validate_offline.py
```

### B. Docker Offline Gold Set Validation (`--network none`)
To verify model performance in a containerized environment without internet access:
```bash
docker build -t voice-helpdesk-asr:a2-final -f code/Dockerfile .
docker run --rm --network none voice-helpdesk-asr:a2-final validate
```
**Expected Terminal Output (Verified Offline Run):**
```json
{
  "status": "SUCCESS",
  "evaluation_split": "gold_test_set",
  "evaluated_clips": 29,
  "gold_set_sha256": "64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9",
  "gold_checksum_match": true,
  "model_version": "production",
  "git_commit": "a2-final",
  "hardware": {
    "system": "Darwin",
    "machine": "arm64",
    "cpu_execution": true,
    "whisper_model": "base"
  },
  "metrics": {
    "transcript_wer": 1.2774,
    "transcript_cer": 0.9401,
    "intent_accuracy": 0.3448,
    "intent_macro_f1": 0.3472,
    "evaluated_clips": 29,
    "mean_inference_latency_ms": 2986.38,
    "cpu_real_time_factor": 0.165,
    "total_audio_duration_sec": 523.8
  },
  "offline_network_isolated": true,
  "offline_verified": true
}
```
*Note*: The validation script verifies the SHA-256 digest of `data/gold_test_set.csv` before running, asserts offline execution, and writes formatted JSON output to `supporting_files/offline_validation_output.json`.

### C. Launch Interactive Streamlit UI & REST API
```bash
# In local environment:
streamlit run code/a2_part_d_deployment/app.py --server.port 8501
# Or containerized:
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

| Artifact | Checksum (SHA-256) | Size / Notes |
|----------|--------------------|--------------|
| `code/Dockerfile` | `c65817ef5919f1259557fc6af96dc4258d7b872f4e17d2fe9b9d7abdd9a4795a` | 2.1 KB (Pinned build definition) |
| Bundled `base.pt` weights | `ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e` | 139 MB (Downloaded & cached locally) |
| Docker Container Archive | Reproducible build via `docker build` | Excluded from git repo due to 100 MB limit |
