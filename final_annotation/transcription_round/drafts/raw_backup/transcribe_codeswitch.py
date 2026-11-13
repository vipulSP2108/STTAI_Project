"""Resume fresh A2 speech transcription with time-local en/hi/gu detection.

Docker mounts: this directory /work (rw), recordings /audio (ro), external
model cache /model-cache (rw). Does not import or submit Label Studio annotations.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import time
from urllib.parse import unquote

import numpy as np
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
from huggingface_hub import HfApi, snapshot_download

HERE = Path(__file__).resolve().parent
REPOSITORIES = {"turbo": "dropbox-dash/faster-whisper-large-v3-turbo",
                "large-v3": "Systran/faster-whisper-large-v3"}
ALLOWED = {"<|en|>", "<|hi|>", "<|gu|>"}


def atomic_json(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


class RestrictedLanguageModel:
    """Delegate inference, restricting only language detection to the corpus languages."""
    def __init__(self, inner):
        self.inner = inner

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def detect_language(self, *args, **kwargs):
        batches = self.inner.detect_language(*args, **kwargs)
        filtered = []
        for predictions in batches:
            allowed = [(token, float(score)) for token, score in predictions if token in ALLOWED]
            total = sum(score for _, score in allowed)
            if not total:
                raise RuntimeError("No supported language returned by decoder")
            filtered.append([(token, score / total) for token, score in allowed])
        return filtered


def script_counts(text):
    return {"latin": len(re.findall(r"[A-Za-z]", text)),
            "devanagari": len(re.findall(r"[\u0900-\u097f]", text)),
            "gujarati": len(re.findall(r"[\u0a80-\u0aff]", text)),
            "arabic": len(re.findall(r"[\u0600-\u06ff]", text))}


def save(path, text_path, config, completed, tasks):
    rows = [completed[t["clip_id"]] for t in tasks if t["clip_id"] in completed]
    atomic_json(path, {"description": "Fresh ASR drafts with local English/Hindi/Gujarati language detection; not human-verified.",
                       "configuration": config, "completed_count": len(rows), "target_count": len(tasks), "transcripts": rows})
    lines = ["A2 — FRESH ENGLISH / HINDI / GUJARATI TRANSCRIPT DRAFTS", "",
             f"Completed: {len(rows)}/{len(tasks)}. Machine drafts; no human verification claimed.",
             "Roman / Devanagari / Gujarati scripts are retained from the decoded speech.",
             "Saved Label Studio annotations and methodology documents were not changed.", ""]
    for row in rows:
        lines.extend(["=" * 76, f"{row['number']:03d}/141 | {row['clip_id']} | {row['uuid']}",
                      "Review flags: " + (", ".join(row["review_flags"]) or "none automatically detected; accuracy not guaranteed"),
                      "", row["transcript"] or "[NO TRANSCRIPT RETURNED]", ""])
    text_path.write_text("\n".join(lines), encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=REPOSITORIES, default="turbo")
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    parser.add_argument("--window", type=float, default=8.0)
    parser.add_argument("--overlap", type=float, default=4.0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output-stem", help="Separate output name for a new pass; existing results are preserved")
    args = parser.parse_args()
    if not 0 <= args.overlap < args.window:
        parser.error("overlap must be nonnegative and smaller than window")
    tasks = json.loads((HERE / "A2_141_ASR_TRANSCRIPTS.json").read_text(encoding="utf-8"))["transcripts"]
    cache = Path("/model-cache")
    pin_file = cache / f"{args.model}_pin.json"
    repo = REPOSITORIES[args.model]
    if pin_file.exists():
        pin = json.loads(pin_file.read_text())
        if pin["repository"] != repo:
            raise RuntimeError("Cached repository mismatch")
    else:
        pin = {"repository": repo, "revision": HfApi().model_info(repo).sha}
        atomic_json(pin_file, pin)
    print(f"Model {repo}@{pin['revision']}", flush=True)
    directory = snapshot_download(repo, revision=pin["revision"], local_dir=str(cache / args.model),
                                  allow_patterns=["config.json", "model.bin", "tokenizer.json", "preprocessor_config.json", "vocabulary.*"])
    compute = "int8_float16" if args.device == "cuda" else "int8"
    config = {"model": pin, "device": args.device, "compute_type": compute,
              "window_seconds": args.window, "overlap_seconds": args.overlap,
              "allowed_languages": ["en", "hi", "gu"], "task": "transcribe", "beam_size": 5,
              "temperature": 0.0, "vad_filter": False, "word_timestamps": True,
              "condition_on_previous_text": False, "language": None,
              "packages": {name: importlib.metadata.version(name) for name in ["faster-whisper", "ctranslate2"]}}
    stem = args.output_stem or f"A2_141_CODESWITCH_{args.model.upper()}"
    if Path(stem).name != stem or stem in {".", ".."}:
        parser.error("output-stem must be a filename without directory components")
    output, text_output = HERE / f"{stem}.json", HERE / f"{stem}.txt"
    completed = {}
    if output.exists():
        previous = json.loads(output.read_text(encoding="utf-8"))
        if previous["configuration"] != config:
            raise RuntimeError("Existing results have different decoding settings; preserve them before changing options")
        completed = {r["clip_id"]: r for r in previous["transcripts"]}
    model = WhisperModel(directory, device=args.device, compute_type=compute, cpu_threads=6, local_files_only=True)
    model.model = RestrictedLanguageModel(model.model)
    count = 0
    for task in tasks:
        relative = unquote(task["audio"].split("?d=final_annotation/annotator_1/records/", 1)[1])
        audio_path = (Path("/audio") / relative).resolve()
        if not audio_path.is_relative_to(Path("/audio")):
            raise RuntimeError("Unsafe audio path")
        checksum = hashlib.sha256(audio_path.read_bytes()).hexdigest()
        if task["clip_id"] in completed:
            if completed[task["clip_id"]]["audio_sha256"] != checksum:
                raise RuntimeError("Source audio changed")
            continue
        start_time = time.perf_counter()
        audio = decode_audio(str(audio_path), sampling_rate=16000)
        duration = len(audio) / 16000
        words, chunks, flags = [], [], []
        position = 0.0
        while position < duration:
            end = min(duration, position + args.window)
            chunk = audio[round(position * 16000):round(end * 16000)]
            segments, info = model.transcribe(chunk, language=None, multilingual=True, task="transcribe",
                                              beam_size=5, temperature=0.0, condition_on_previous_text=False,
                                              vad_filter=False, word_timestamps=True, max_new_tokens=160)
            segments = list(segments)
            owner_start = 0 if position == 0 else position + args.overlap / 2
            owner_end = duration if end == duration else end - args.overlap / 2
            local_words = []
            for segment in segments:
                if segment.compression_ratio > 2.4 or segment.avg_logprob < -1.0:
                    flags.append("low_confidence_or_repetition")
                for word in segment.words or []:
                    global_start = max(0.0, position + word.start)
                    global_end = min(duration, position + word.end)
                    midpoint = (global_start + global_end) / 2
                    entry = {"start": round(global_start, 3), "end": round(global_end, 3),
                             "word": word.word, "probability": word.probability}
                    local_words.append(entry)
                    if owner_start <= midpoint < owner_end or (end == duration and midpoint == duration):
                        words.append(entry)
            chunks.append({"start": position, "end": end, "detected_language": info.language,
                           "language_probabilities": info.all_language_probs,
                           "text": " ".join(s.text.strip() for s in segments), "words": local_words})
            if end == duration:
                break
            position += args.window - args.overlap
        text = "".join(w["word"] for w in words).strip()
        counts = script_counts(text)
        if not text:
            flags.append("empty_output")
        if task["clip_id"] == "P9_41" and not counts["devanagari"]:
            flags.append("user_reported_Hindi_but_no_Devanagari_returned")
        if task["clip_id"] == "P9_41":
            # The Hindi-hinted comparison located two candidate Hindi passages.
            # Presence of Devanagari elsewhere is not sufficient to pass this clip.
            for label, begin, finish in [("first", 11.0, 16.5), ("second", 27.5, 33.0)]:
                passage = "".join(w["word"] for w in words if begin <= (w["start"] + w["end"]) / 2 <= finish)
                if not script_counts(passage)["devanagari"]:
                    flags.append(f"{label}_candidate_Hindi_passage_missing_Devanagari")
        if counts["arabic"]:
            flags.append("unexpected_Arabic_script")
        completed[task["clip_id"]] = {
            **{k: task[k] for k in ("number", "clip_id", "uuid", "assignment_group", "audio")},
            "transcript": text, "status": "machine_draft", "verified_against_audio_for_this_export": False,
            "audio_sha256": checksum, "duration_seconds": round(duration, 3),
            "decode_seconds": round(time.perf_counter() - start_time, 2),
            "script_counts": counts, "review_flags": sorted(set(flags)), "words": words, "chunks": chunks,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        save(output, text_output, config, completed, tasks)
        print(f"[{len(completed)}/141] {task['clip_id']} {counts} decode={completed[task['clip_id']]['decode_seconds']}s flags={sorted(set(flags))}", flush=True)
        count += 1
        if args.limit and count >= args.limit:
            break
    print(f"Saved {len(completed)}/141 fresh drafts to {text_output}", flush=True)


if __name__ == "__main__":
    main()
