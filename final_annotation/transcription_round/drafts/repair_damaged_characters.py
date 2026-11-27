"""Re-decode only audio around literal U+FFFD characters; save candidates, not annotations."""
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import unquote

from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio

HERE = Path(__file__).resolve().parent
OUT = HERE / "character_repair_candidates.json"


def save(value):
    temp = OUT.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(OUT)


def main():
    source = HERE / "raw_backup/A2_141_WHISPER_PASS_2.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    results = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "model": "Systran/faster-whisper-large-v3@edaa852ec7e145841d8ffdb056a99866b5f0a478",
        "description": "Audio-grounded repair candidates; no human verification claimed. No 160-token cap.",
        "regions": [],
    }
    if results["source_sha256"] != hashlib.sha256(source.read_bytes()).hexdigest():
        raise RuntimeError("Repair source changed")
    completed = {(r["clip_id"], r["start"], r["end"]) for r in results["regions"]}
    model = WhisperModel("/model-cache/large-v3", device="cuda", compute_type="int8_float16",
                         cpu_threads=6, local_files_only=True)
    for row in data["transcripts"]:
        bad = [(i, w) for i, w in enumerate(row["words"]) if "\ufffd" in w["word"]]
        if not bad:
            continue
        relative = unquote(row["audio"].split("?d=final_annotation/annotator_1/records/", 1)[1])
        audio_file = Path("/audio") / relative
        if hashlib.sha256(audio_file.read_bytes()).hexdigest() != row["audio_sha256"]:
            raise RuntimeError("Audio changed: " + row["clip_id"])
        audio = decode_audio(str(audio_file), sampling_rate=16000)
        duration = len(audio) / 16000
        regions = []
        for i, w in bad:
            begin, end = round(max(0, w["start"] - 2.5), 3), round(min(duration, w["end"] + 2.5), 3)
            if regions and begin <= regions[-1][1] + 0.6:
                regions[-1][1] = max(regions[-1][1], end)
                regions[-1][2].append(i)
            else:
                regions.append([begin, end, [i]])
        for begin, end, indices in regions:
            if (row["clip_id"], begin, end) in completed:
                continue
            context = " ".join(w["word"] for w in row["words"] if begin <= (w["start"] + w["end"]) / 2 <= end)
            gu = sum("\u0a80" <= c <= "\u0aff" for c in context)
            hi = sum("\u0900" <= c <= "\u097f" for c in context)
            language = "gu" if gu > hi else "hi"
            start_time = time.perf_counter()
            segments, info = model.transcribe(audio[round(begin*16000):round(end*16000)], language=language,
                                              task="transcribe", beam_size=5, temperature=0.0,
                                              condition_on_previous_text=False, vad_filter=False,
                                              word_timestamps=False)
            segments = list(segments)
            text = " ".join(s.text.strip() for s in segments)
            item = {"number": row["number"], "clip_id": row["clip_id"], "start": begin, "end": end,
                    "language_hint": language, "damaged_word_indices": indices,
                    "bad_words": [row["words"][i]["word"] for i in indices],
                    "original_context": context, "text": text,
                    "decode_seconds": round(time.perf_counter()-start_time, 2),
                    "segments": [{"start": begin+s.start, "end": min(end, begin+s.end), "text": s.text} for s in segments]}
            results["regions"].append(item)
            save(results)
            print(f"[{len(results['regions'])}] #{row['number']} {row['clip_id']} {begin}-{end} {language} bad_left={text.count(chr(0xfffd))}", flush=True)


if __name__ == "__main__":
    main()
