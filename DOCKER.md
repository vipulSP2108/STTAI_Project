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
**Expected Terminal Output:**
```json
{
  "status": "SUCCESS",
  "evaluation_split": "gold_test_set",
  "evaluated_clips": 29,
  "gold_set_sha256": "64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9",
  "gold_checksum_match": true,
  "model_version": "production",
  "git_commit": "5b41413",
  "metrics": {
    "transcript_wer": 1.2774,
    "transcript_cer": 0.9414,
    "intent_accuracy": 0.3448,
    "intent_macro_f1": 0.3218,
    "evaluated_clips": 29,
    "mean_inference_latency_ms": 2855.2,
    "cpu_real_time_factor": 0.243,
    "total_audio_duration_sec": 523.8
  },
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

| Artifact | Checksum (SHA-256) | Size |
|----------|--------------------|------|
| `code/Dockerfile` | `e9f2a41bc...` | 2.1 KB |
| `docker_image.tar.gz` (Archive) | Cataloged in `artefacts/` | 1.85 GB |
| Bundled `base.pt` weights | `a3f9104cc...` | 139 MB |
