"""Exercise the revised REST routes with a real offline ASR request."""

import argparse
from io import BytesIO
import json
from pathlib import Path

from fastapi.testclient import TestClient
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

from revised_api import app
from revised_data import CLASSES, check_wav


def stereo_44100(audio):
    _, mono = wavfile.read(audio)
    converted = resample_poly(mono.astype(np.float32), 441, 160)
    pcm = np.clip(converted, -32768, 32767).astype(np.int16)
    wav = BytesIO()
    wavfile.write(wav, 44100, np.column_stack((pcm, pcm)))
    return wav.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    args = parser.parse_args()
    duration = check_wav(args.audio)
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200 and health.json()["status"] == "HEALTHY"
        version = client.get("/version")
        assert version.status_code == 200 and version.json()["model_version"]
        response = client.post("/predict", files={"file": ("sample.wav", args.audio.read_bytes(), "audio/wav")})
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["transcript"] and result["intent"] in CLASSES
        assert result["model_version"] == version.json()["model_version"]
        assert 0 <= result["confidence"] <= 1 and result["latency_ms"] > 0
        stereo = client.post("/predict", files={"file": ("stereo.wav", stereo_44100(args.audio), "audio/wav")})
        assert stereo.status_code == 200, stereo.text
        assert stereo.json()["transcript"] and stereo.json()["intent"] in CLASSES
        assert abs(stereo.json()["audio_seconds"] - duration) < 0.01
        assert client.post("/predict", files={"file": ("sample.wav", b"bad", "audio/wav")}).status_code == 400
    print(json.dumps({"status": "pass", "audio_seconds": duration, "version": version.json(),
                      "intent": result["intent"], "latency_ms": result["latency_ms"],
                      "stereo_44100_http": stereo.status_code}, indent=2))


if __name__ == "__main__":
    main()
