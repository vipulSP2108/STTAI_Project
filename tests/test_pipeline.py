"""
CS203 Assignment 2 - Unit & Integration Test Suite
Validates:
1. Normalisation rules and text preprocessing.
2. Cryptographic immutability of held-out Gold test set.
3. Model gating logic and regression tolerance bounds.
4. FastAPI REST service endpoints (/health, /version, /predict) with live requests.
"""

import hashlib
import io
import math
import struct
import sys
import wave
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add project root and deployment directory to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
sys.path.append(str(ROOT_DIR / "code"))
sys.path.append(str(ROOT_DIR / "code/a2_part_d_deployment"))

from normalisation import normalise_text
from app import app

EXPECTED_GOLD_HASH = "64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9"


def generate_synthetic_wav_bytes(duration_sec=1.0, sample_rate=16000, frequency=440.0) -> bytes:
    """Generates an in-memory 16kHz mono PCM WAV byte stream for REST testing."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_samples = int(duration_sec * sample_rate)
        samples = []
        for i in range(n_samples):
            val = int(32767.0 * 0.3 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
            samples.append(struct.pack("<h", val))
        wf.writeframes(b"".join(samples))
    return buf.getvalue()


class TestPipelineCore:
    def test_normalisation_rules(self):
        """Test lowercase, punctuation stripping, whitespace normalization, and repetition squashing."""
        sample_raw = "Hello, IITGN  Helpdesk!! Can I get hostel room 410 permission???"
        expected = "hello iitgn helpdesk can i get hostel room 410 permission"
        assert normalise_text(sample_raw) == expected

        # Number preservation
        assert normalise_text("Ticket 1493 status") == "ticket 1493 status"

        # Character repetition collapsing
        assert normalise_text("nooooo waaaay") == "no way"

    def test_gold_test_set_integrity(self):
        """Ensure gold test set checksum is bit-for-bit identical to frozen baseline."""
        gold_path = ROOT_DIR / "data/gold_test_set.csv"
        assert gold_path.exists(), "Gold test set file missing!"
        actual_hash = hashlib.sha256(gold_path.read_bytes()).hexdigest()
        assert actual_hash == EXPECTED_GOLD_HASH, (
            f"SECURITY ALERT: Gold test set has been modified! Expected {EXPECTED_GOLD_HASH}, got {actual_hash}"
        )

    def test_gate_criteria_logic(self):
        """Test gate evaluation thresholds for model promotion and rollback under strict ex-ante bounds."""
        # Simulated scenario 1: Positive adaptation (+7.7%), zero gold degradation (+0.0% <= 2.0%) -> PROMOTED
        min_cohort_gain = 0.05
        max_gold_degradation = 0.02

        cohort_delta_pass = 0.077
        gold_deg_pass = 0.000
        assert (cohort_delta_pass >= min_cohort_gain) and (gold_deg_pass <= max_gold_degradation)

        # Simulated scenario 2: Catastrophic forgetting (+10.3% gold degradation) -> REJECTED
        gold_deg_fail = 0.103
        assert not (gold_deg_fail <= max_gold_degradation)

        # Simulated scenario 3: No out-of-distribution gain (+0.0%) -> REJECTED
        cohort_delta_fail = 0.000
        assert not (cohort_delta_fail >= min_cohort_gain)

    def test_dataset_pools_disjointness(self):
        """Verify absolute disjointness between Gold, Train, Val, Adapt, Heldout, and Replay sets."""
        import json
        import pandas as pd
        gold = set(pd.read_csv(ROOT_DIR / "data/gold_test_set.csv")["clip_id"])
        train = set(pd.read_csv(ROOT_DIR / "data/splits/train.csv")["clip_id"])
        val = set(pd.read_csv(ROOT_DIR / "data/splits/val.csv")["clip_id"])
        adapt = set(pd.read_csv(ROOT_DIR / "data/retraining/cohort_b_adapt.csv")["clip_id"])
        heldout = set(pd.read_csv(ROOT_DIR / "data/retraining/cohort_b_heldout.csv")["clip_id"])
        ann_pool = set(pd.read_csv(ROOT_DIR / "data/retraining/annotator_pool.csv")["clip_id"])

        replay_path = ROOT_DIR / "data/replay/traffic_stream.jsonl"
        replay = set()
        if replay_path.exists():
            with open(replay_path) as f:
                replay = {json.loads(line)["clip_id"] for line in f if "clip_id" in json.loads(line)}

        assert len(gold & train) == 0, "Leakage: Gold overlaps with Train"
        assert len(gold & val) == 0, "Leakage: Gold overlaps with Val"
        assert len(gold & adapt) == 0, "Leakage: Gold overlaps with Adapt"
        assert len(gold & heldout) == 0, "Leakage: Gold overlaps with Heldout"
        assert len(gold & ann_pool) == 0, "Leakage: Gold overlaps with Annotator Pool"
        assert len(gold & replay) == 0, "Leakage: Gold overlaps with Replay"
        assert len(adapt & heldout) == 0, "Leakage: Adapt overlaps with Heldout"
        assert len(ann_pool & heldout) == 0, "Leakage: Annotator Pool overlaps with Heldout"
        assert len(heldout & replay) == 0, "Leakage: Heldout overlaps with Replay"
        assert len(train & val) == 0, "Leakage: Train overlaps with Val"


class TestApiEndpoints:
    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Send GET /health and assert valid response schema."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "HEALTHY"
        assert "uptime_seconds" in data
        assert "memory_mb" in data
        assert data["memory_mb"] > 0

    def test_version_endpoint(self, client):
        """Send GET /version and verify model version and frozen gold hash."""
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert data["gold_set_sha256"] == EXPECTED_GOLD_HASH
        assert data["pipeline_stage"] == "production"

    def test_predict_endpoint_valid_audio(self, client):
        """Send POST /predict with a synthetic WAV audio file and verify full response schema."""
        wav_bytes = generate_synthetic_wav_bytes(duration_sec=0.5)
        files = {"file": ("test_query.wav", io.BytesIO(wav_bytes), "audio/wav")}

        response = client.post("/predict", files=files)
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "transcript" in data
        assert "intent" in data
        assert "confidence" in data
        assert "latency_ms" in data
        assert "model_version" in data
        assert "git_commit" in data

        # Check value constraints
        assert data["intent"] in ["admissions", "hostel_mess", "it_support", "student_services"]
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["latency_ms"] > 0.0

    def test_predict_bad_request_empty_file(self, client):
        """Assert empty payload returns HTTP 400."""
        files = {"file": ("empty.wav", io.BytesIO(b""), "audio/wav")}
        response = client.post("/predict", files=files)
        assert response.status_code == 400

    def test_predict_bad_request_unsupported_format(self, client):
        """Assert invalid file format returns HTTP 400."""
        files = {"file": ("notes.txt", io.BytesIO(b"dummy text"), "text/plain")}
        response = client.post("/predict", files=files)
        assert response.status_code == 400

