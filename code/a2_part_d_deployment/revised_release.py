"""Offline CPU pipeline (indic-v2): language routing -> Indic Whisper ASR -> intent router.

  1. Language router (router_v2.LangRouter): Whisper-base language probabilities -> en / hi / gu.
  2. ASR: hi -> vasista22/whisper-hindi-small, gu -> vasista22/whisper-gujarati-base (both CTranslate2
     int8, pinned revisions converted at image build), en -> Systran/faster-whisper-base. Greedy,
     VAD on, no prompt (the old domain prompt caused copy loops).
  3. Intent router (router_v2.IntentRouter), trained at build time on ASR text of training speakers.

Commands: train-router | check-audio | validate [--output FILE]
"""

import argparse
import csv
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import pickle
import resource
from time import perf_counter
import unicodedata

from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
import jiwer
import numpy as np

from revised_data import ROOT, check_sample, examples, release_rows
from router_v2 import Embedder, IntentRouter, LangRouter, clean_text, route_label


AUDIO_DIR = Path(os.getenv("RELEASE_AUDIO_DIR", ROOT / "revised_audio"))
MODEL_DIR = Path(os.getenv("MODEL_DIR", "/opt/models"))
ROUTER_PATH = ROOT / "routers_v2.pkl"
MODEL_VERSION = "indic-v2-lid-router-b3-expert"
REVISIONS = {
    "faster-whisper-base": "Systran/faster-whisper-base@ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66",
    "whisper-hindi-small": "vasista22/whisper-hindi-small@fb4a24afc20c42906deed31c3689e4be31da41fe",
    "whisper-gujarati-base": "vasista22/whisper-gujarati-base@59c972a6f00f529efc7c9b631dff338157561ed9",
    "minilm": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2@e8f8c211226b894fcb81acc59f3b34ba3efd5f42",
}
ASR_DIRS = {"en": "whisper-base", "hi": "whisper-hindi-ct2", "gu": "whisper-gujarati-ct2"}


def normalise(text):
    text = unicodedata.normalize("NFKC", text or "").casefold()
    return " ".join("".join(" " if unicodedata.category(c)[0] in "PS" else c for c in text).split())


def train_router():
    groups = release_rows()
    intent = IntentRouter(Embedder(str(MODEL_DIR / "minilm")))
    selection = intent.select_and_fit(groups["train"], groups["validation"])
    feats = json.loads((ROOT / "model/data/reports/lid_features.json").read_text())
    lang = LangRouter().fit(feats, groups["train"] + groups["validation"])
    with open(ROUTER_PATH, "wb") as f:
        pickle.dump({"intent": intent, "lang": lang, "selection": selection}, f)
    print(f"Trained routers on {len(groups['train'])} train + {len(groups['validation'])} validation clips; {selection}")


@lru_cache(maxsize=1)
def get_models():
    for d in ASR_DIRS.values():
        for name in ("config.json", "model.bin", "tokenizer.json"):
            if not (MODEL_DIR / d / name).is_file():
                raise FileNotFoundError(MODEL_DIR / d / name)
    asr = {k: WhisperModel(str(MODEL_DIR / d), device="cpu", compute_type="int8", cpu_threads=2, local_files_only=True)
           for k, d in ASR_DIRS.items()}
    with open(ROUTER_PATH, "rb") as f:
        bundle = pickle.load(f)
    bundle["intent"].emb = Embedder(str(MODEL_DIR / "minilm"))
    return asr, bundle["intent"], bundle["lang"]


def version():
    return {
        "model_version": MODEL_VERSION,
        "asr_revision": REVISIONS["faster-whisper-base"].split("@")[1],
        "revisions": REVISIONS,
        "git_commit": os.getenv("GIT_COMMIT", "unknown"),
        "source_tree": os.getenv("SOURCE_TREE", "unspecified"),
    }


def predict(audio):
    asr, intent_router, lang_router = get_models()
    start = perf_counter()
    if isinstance(audio, Path):
        audio = decode_audio(str(audio), sampling_rate=16000)
    lang, lang_probs = lang_router.predict(LangRouter.features(asr["en"], audio))
    segments, info = asr[lang].transcribe(audio, language=lang, beam_size=1, temperature=0.0,
                                        condition_on_previous_text=False, vad_filter=True)
    transcript = " ".join(segment.text.strip() for segment in segments).strip()
    intent, confidence = None, 0.0
    if clean_text(transcript):
        classes, probabilities = intent_router.predict_proba([transcript])
        best = int(probabilities[0].argmax())
        intent, confidence = str(classes[best]), float(probabilities[0][best])
    elapsed = perf_counter() - start
    duration = len(audio) / 16000
    return {
        **version(),
        "transcript": transcript,
        "intent": intent,
        "confidence": round(confidence, 4),
        "language": lang,
        "language_probabilities": lang_probs,
        "audio_seconds": duration,
        "latency_ms": round(elapsed * 1000, 2),
        "rtf": round(elapsed / duration, 4) if duration else None,
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
        predictions.append({"uuid": row["uuid"], "expected_intent": row["intent"],
                            "expected_route": route_label(row["languages"]), **result})
        print(f"Decoded test clip {index}/{len(groups['test'])}", flush=True)

    actual = [row["expected_intent"] for row in predictions]
    predicted = [row["intent"] for row in predictions]
    labels = sorted(set(actual))
    intent_f1 = []
    for label in labels:
        tp = sum(a == p == label for a, p in zip(actual, predicted))
        support = actual.count(label) + predicted.count(label)
        intent_f1.append(2 * tp / support if support else 0.0)
    latencies = [row["latency_ms"] for row in predictions]
    with_ref = [(normalise(r["reference"]), normalise(p["transcript"])) for r, p in zip(groups["test"], predictions) if r["reference"]]
    payload = {
        **version(),
        "split": "revised_release_test",
        "speaker_split_sha256": hashlib.sha256((ROOT / "model/data/splits/release_speakers.json").read_bytes()).hexdigest(),
        "sample_count": len(actual),
        "intent_accuracy": sum(a == p for a, p in zip(actual, predicted)) / len(actual),
        "intent_macro_f1": sum(intent_f1) / len(labels),
        "language_route_accuracy": float(np.mean([p["language"] == p["expected_route"] for p in predictions])),
        "wer": jiwer.wer([r for r, _ in with_ref], [h for _, h in with_ref]) if with_ref else None,
        "cer": jiwer.cer([r for r, _ in with_ref], [h for _, h in with_ref]) if with_ref else None,
        "wer_reference_count": len(with_ref),
        "wer_status": "human Round T transcripts" if with_ref else "not computed: no human transcripts bundled (curated text withdrawn)",
        "cpu_latency_ms_p50": float(np.percentile(latencies, 50)),
        "cpu_latency_ms_p95": float(np.percentile(latencies, 95)),
        "cpu_rtf": sum(latencies) / (1000 * sum(row["audio_seconds"] for row in predictions)),
        "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2),
        "predictions": [{k: p[k] for k in ("uuid", "expected_intent", "intent", "confidence", "expected_route", "language", "latency_ms")}
                        for p in predictions],
    }
    if output:
        output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "predictions"}, indent=2))


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
