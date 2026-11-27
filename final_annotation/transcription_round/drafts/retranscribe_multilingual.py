"""Resume audio-grounded multilingual A2 drafts in a container; never submit annotations.

Mount this directory as /work, annotator_1/records read-only as /audio, and an
external model cache as /model-cache. The existing A2 export supplies task IDs only;
its transcript strings are never used as decoding prompts or references.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import unquote

from faster_whisper import WhisperModel
from huggingface_hub import HfApi, snapshot_download


HERE = Path(__file__).resolve().parent
MODEL_REPO = "dropbox-dash/faster-whisper-large-v3-turbo"
OUTPUT = HERE / "A2_141_MULTILINGUAL_TRANSCRIPTS.json"
TEXT = HERE / "A2_141_MULTILINGUAL_TRANSCRIPTS.txt"
PIN = Path("/model-cache/turbo_pin.json")


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def scripts(text):
    return {
        "latin_letters": len(re.findall(r"[A-Za-z]", text)),
        "devanagari_characters": len(re.findall(r"[\u0900-\u097f]", text)),
        "gujarati_characters": len(re.findall(r"[\u0a80-\u0aff]", text)),
    }


def save(config, completed, tasks):
    ordered = [completed[t["clip_id"]] for t in tasks if t["clip_id"] in completed]
    atomic_json(OUTPUT, {
        "description": "Fresh multilingual ASR drafts decoded from audio; not human-verified or submitted.",
        "configuration": config,
        "completed_count": len(ordered), "target_count": len(tasks),
        "transcripts": ordered,
    })
    lines = ["A2 — FRESH MULTILINGUAL ASR DRAFTS", "",
             f"Completed: {len(ordered)}/{len(tasks)}. Machine drafts; audio review still required.",
             "English/Hindi/Gujarati may occur within the same recording. Original decoded scripts retained.",
             "No existing Label Studio submissions or methodology documents were changed.", ""]
    for row in ordered:
        lines.extend(["=" * 76, f"{row['number']:03d}/141 | {row['clip_id']} | {row['uuid']}",
                      f"Audio: {row['audio']}",
                      "Review flags: " + (", ".join(row["review_flags"]) or "none automatically detected; not proof of accuracy"),
                      "", row["transcript"] or "[NO TRANSCRIPT RETURNED — LISTEN AND REVIEW]", ""])
    TEXT.write_text("\n".join(lines), encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--clip-id")
    parser.add_argument("--chunk-length", type=int, default=12)
    args = parser.parse_args()
    tasks = json.loads((HERE / "A2_141_ASR_TRANSCRIPTS.json").read_text(encoding="utf-8"))["transcripts"]
    if PIN.exists():
        pin = json.loads(PIN.read_text())
        if pin["repository"] != MODEL_REPO:
            raise RuntimeError("Unexpected cached model repository")
    else:
        pin = {"repository": MODEL_REPO, "revision": HfApi().model_info(MODEL_REPO).sha}
        atomic_json(PIN, pin)
    print(f"Model: {MODEL_REPO}@{pin['revision']}", flush=True)
    model_dir = snapshot_download(MODEL_REPO, revision=pin["revision"], local_dir="/model-cache/turbo",
                                  allow_patterns=["config.json", "model.bin", "tokenizer.json", "preprocessor_config.json", "vocabulary.*"])
    options = dict(language=None, task="transcribe", multilingual=True, beam_size=5,
                   temperature=0.0, condition_on_previous_text=False, vad_filter=False,
                   chunk_length=args.chunk_length)
    config = {"model": pin, "compute_type": "int8", "options": options,
              "timestamp": datetime.now(timezone.utc).isoformat()}
    completed = {}
    if OUTPUT.exists():
        old = json.loads(OUTPUT.read_text(encoding="utf-8"))
        previous = old["configuration"]
        if previous["model"] != pin or previous["options"] != options:
            raise RuntimeError("Existing results use different model/options; preserve them before a different run")
        completed = {r["clip_id"]: r for r in old["transcripts"]}
    model = WhisperModel(model_dir, device="cpu", compute_type="int8", cpu_threads=6, local_files_only=True)
    selected = [t for t in tasks if not args.clip_id or t["clip_id"] == args.clip_id]
    if not selected:
        raise ValueError("Requested clip does not exist in the A2 task list")
    count = 0
    for task in selected:
        relative = unquote(task["audio"].split("?d=final_annotation/annotator_1/records/", 1)[1])
        audio = (Path("/audio") / relative).resolve()
        if not audio.is_relative_to(Path("/audio")):
            raise ValueError("Audio path escapes mounted recordings directory")
        checksum = hashlib.sha256(audio.read_bytes()).hexdigest()
        if task["clip_id"] in completed:
            if completed[task["clip_id"]]["audio_sha256"] != checksum:
                raise RuntimeError("Audio changed since previous decode: " + task["clip_id"])
            continue
        start = time.perf_counter()
        segments, info = model.transcribe(str(audio), **options)
        segments = list(segments)
        text = " ".join(s.text.strip() for s in segments).strip()
        counts = scripts(text)
        flags = []
        if not text:
            flags.append("empty_output")
        # User explicitly heard Hindi in this clip despite its old English-only tag.
        if task["clip_id"] == "P9_41" and not counts["devanagari_characters"]:
            flags.append("user_reported_Hindi_but_no_Devanagari_returned")
        if any(s.avg_logprob < -1.0 or s.compression_ratio > 2.4 for s in segments):
            flags.append("low_confidence_or_repetition")
        completed[task["clip_id"]] = {
            **{k: task[k] for k in ("number", "clip_id", "uuid", "assignment_group", "audio")},
            "transcript": text, "status": "machine_draft", "verified_against_audio_for_this_export": False,
            "audio_sha256": checksum, "decode_seconds": round(time.perf_counter() - start, 2),
            "duration_seconds": round(info.duration, 3), "initial_detected_language": info.language,
            "script_counts": counts, "review_flags": flags,
            "segments": [{"start": s.start, "end": s.end, "text": s.text,
                          "avg_logprob": s.avg_logprob, "no_speech_prob": s.no_speech_prob,
                          "compression_ratio": s.compression_ratio} for s in segments],
        }
        save(config, completed, tasks)
        print(f"[{len(completed)}/141] {task['clip_id']} {counts} flags={flags}", flush=True)
        count += 1
        if args.limit and count >= args.limit:
            break
    print(f"Saved {len(completed)} drafts; existing annotations unchanged.", flush=True)


if __name__ == "__main__":
    main()
