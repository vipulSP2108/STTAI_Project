"""Offline CPU transcription, intent routing, and release validation."""

import argparse
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import resource
from time import perf_counter
import unicodedata

from faster_whisper import WhisperModel
import jiwer
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from revised_data import ROOT, check_sample, examples, release_rows


AUDIO_DIR = Path(os.getenv("RELEASE_AUDIO_DIR", ROOT / "revised_audio"))
ROUTER_PATH = ROOT / "intent_router.joblib"
ASR_PATH = Path("/opt/whisper-base")
MODEL_VERSION = "revised-whisper-base-char-tfidf-v1"
MODEL_REVISION = "ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66"


def normalise(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    return " ".join("".join(" " if unicodedata.category(c).startswith("P") else c for c in text).split())


def train_router():
    rows = release_rows()["train"]
    router = make_pipeline(
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True),
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
    )
    router.fit([normalise(row["reference"]) for row in rows], [row["intent"] for row in rows])
    joblib.dump(router, ROUTER_PATH)
    print(f"Trained intent router on {len(rows)} revised training references")


@lru_cache(maxsize=1)
def get_models():
    for name in ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt"):
        if not (ASR_PATH / name).is_file():
            raise FileNotFoundError(ASR_PATH / name)
    asr = WhisperModel(str(ASR_PATH), device="cpu", compute_type="int8", cpu_threads=2, local_files_only=True)
    return asr, joblib.load(ROUTER_PATH)


def version():
    return {
        "model_version": MODEL_VERSION,
        "asr_revision": MODEL_REVISION,
        "git_commit": os.getenv("GIT_COMMIT", "unknown"),
        "source_tree": os.getenv("SOURCE_TREE", "unspecified"),
    }


def predict(audio):
    asr, router = get_models()
    start = perf_counter()
    source = str(audio) if isinstance(audio, Path) else audio
    segments, info = asr.transcribe(source, beam_size=1, condition_on_previous_text=False)
    transcript = " ".join(segment.text.strip() for segment in segments).strip()
    text = normalise(transcript)
    intent, confidence = None, 0.0
    if text:
        probabilities = router.predict_proba([text])[0]
        best = int(probabilities.argmax())
        intent, confidence = str(router.classes_[best]), float(probabilities[best])
    elapsed = perf_counter() - start
    return {
        **version(),
        "transcript": transcript,
        "intent": intent,
        "confidence": round(confidence, 4),
        "language": info.language,
        "audio_seconds": info.duration,
        "latency_ms": round(elapsed * 1000, 2),
        "rtf": round(elapsed / info.duration, 4) if info.duration else None,
    }


def check_bundled_audio(groups):
    for row in groups["test"] + examples(groups):
        check_sample(AUDIO_DIR / f"{row['uuid']}.wav", row)


def validate(output):
    groups = release_rows()
    check_bundled_audio(groups)
    get_models()
    predictions = []
    for index, row in enumerate(groups["test"], start=1):
        result = predict(AUDIO_DIR / f"{row['uuid']}.wav")
        predictions.append({"uuid": row["uuid"], "expected_intent": row["intent"], **result})
        print(f"Decoded test clip {index}/{len(groups['test'])}", flush=True)

    references = [normalise(row["reference"]) for row in groups["test"]]
    hypotheses = [normalise(row["transcript"]) for row in predictions]
    actual = [row["expected_intent"] for row in predictions]
    predicted = [row["intent"] for row in predictions]
    labels = sorted(set(actual))
    intent_f1 = []
    for label in labels:
        tp = sum(a == p == label for a, p in zip(actual, predicted))
        support = actual.count(label) + predicted.count(label)
        intent_f1.append(2 * tp / support)
    latencies = [row["latency_ms"] for row in predictions]
    payload = {
        **version(),
        "split": "revised_release_test",
        "speaker_split_sha256": hashlib.sha256((ROOT / "model/data/splits/release_speakers.json").read_bytes()).hexdigest(),
        "sample_count": len(actual),
        "wer": jiwer.wer(references, hypotheses),
        "cer": jiwer.cer(references, hypotheses),
        "intent_accuracy": sum(a == p for a, p in zip(actual, predicted)) / len(actual),
        "intent_macro_f1": sum(intent_f1) / len(labels),
        "cpu_latency_ms_p50": float(np.percentile(latencies, 50)),
        "cpu_latency_ms_p95": float(np.percentile(latencies, 95)),
        "cpu_rtf": sum(latencies) / (1000 * sum(row["audio_seconds"] for row in predictions)),
        "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2),
    }
    if output:
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("train-router", "check-audio", "validate"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "train-router":
        train_router()
    elif args.command == "check-audio":
        check_bundled_audio(release_rows())
    else:
        validate(args.output)


if __name__ == "__main__":
    main()
