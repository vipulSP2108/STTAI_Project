"""Check full-pass coverage/provenance and list machine-draft review priorities."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-root", type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    results = json.loads((here / "A2_141_WHISPER_PASS_2.json").read_text(encoding="utf-8"))
    original = json.loads((here / "A2_141_ASR_TRANSCRIPTS.json").read_text(encoding="utf-8"))["transcripts"]
    rows = results["transcripts"]
    expected = {r["clip_id"]: r for r in original}
    if len(rows) != 141 or len({r["clip_id"] for r in rows}) != 141 or {r["clip_id"] for r in rows} != set(expected):
        raise RuntimeError("Full pass must contain exactly the 141 assigned unique clips")
    if results["completed_count"] != 141 or results["target_count"] != 141:
        raise RuntimeError("Progress counters do not indicate full completion")
    manifest = here.parents[2] / "model/data/metadata/internal_manifest.json"
    hints = {r["uuid"]: r["languages"] for r in json.loads(manifest.read_text(encoding="utf-8-sig"))["manifest"]}
    records, flags_count = [], Counter()
    for row in rows:
        source = expected[row["clip_id"]]
        if any(row[k] != source[k] for k in ["number", "uuid", "audio", "assignment_group"]):
            raise RuntimeError("Task identity mismatch: " + row["clip_id"])
        relative = unquote(row["audio"].split("?d=final_annotation/annotator_1/records/", 1)[1])
        audio = (args.audio_root / relative).resolve()
        if not audio.is_relative_to(args.audio_root.resolve()):
            raise RuntimeError("Audio path escapes supplied root")
        if hashlib.sha256(audio.read_bytes()).hexdigest() != row["audio_sha256"]:
            raise RuntimeError("Audio SHA-256 mismatch: " + row["clip_id"])
        if row["status"] != "machine_draft" or row["verified_against_audio_for_this_export"]:
            raise RuntimeError("Unexpected verification claim")
        flags = list(row["review_flags"])
        text = row["transcript"]
        if not text.strip():
            flags.append("empty_output")
        if "\ufffd" in text:
            flags.append("decoder_replacement_character_requires_repair")
        if "[UNK]" in text:
            flags.append("unresolved_audio_word_marked_UNK")
        counts = row["script_counts"]
        for language, key in [("English", "latin"), ("Hindi", "devanagari"), ("Gujarati", "gujarati")]:
            if language in hints[row["uuid"]] and not counts[key]:
                flags.append("metadata_" + language + "_script_absent_check_audio")
            if language not in hints[row["uuid"]] and counts[key] > 20:
                flags.append(language + "_script_not_in_metadata_check_audio")
        if re.search(r"डि[डट] नॉट|आई वेटेड|फॉर द|लेट मी|एंड चेक|वॉस वर्किंग|आई कैन|आई वांट", text):
            flags.append("possible_English_phonetically_written_in_Devanagari")
        if re.search(r"આઈ વોન્ટ|આઈ કેન|થેન્ક યુ|લેટ મી", text):
            flags.append("possible_English_phonetically_written_in_Gujarati")
        words = row["words"]
        if words and sum(w["probability"] < 0.4 for w in words) / len(words) > 0.25:
            flags.append("many_low_confidence_words")
        for first, second in zip(words, words[1:]):
            a, b = re.sub(r"\W", "", first["word"]).lower(), re.sub(r"\W", "", second["word"]).lower()
            if a and a == b and first["end"] > second["start"]:
                flags.append("possible_duplicate_at_window_boundary")
                break
        flags = sorted(set(flags))
        flags_count.update(flags)
        records.append({"number": row["number"], "clip_id": row["clip_id"], "flags": flags,
                        "script_counts": counts, "word_count": len(text.split())})
    summary = {
        "clip_count": len(rows), "unique_ids_verified": True, "task_mapping_verified": True,
        "all_audio_hashes_verified": True, "nonempty_transcripts": sum(bool(r["transcript"].strip()) for r in rows),
        "audio_minutes": round(sum(r["duration_seconds"] for r in rows) / 60, 2),
        "decode_minutes": round(sum(r["decode_seconds"] for r in rows) / 60, 2),
        "clips_with_review_flags": sum(bool(r["flags"]) for r in records),
        "flag_counts": dict(flags_count), "human_verified": False, "records": records,
    }
    (here / "A2_141_WHISPER_PASS_2_REVIEW.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Whisper pass 2 — coverage and review list", "",
             "All 141 assigned clip IDs and source WAV SHA-256 hashes were checked. No human accuracy verification is claimed.",
             f"Nonempty transcripts: {summary['nonempty_transcripts']}/141. Audio: {summary['audio_minutes']} minutes.",
             f"Clips flagged for review: {summary['clips_with_review_flags']}. Unflagged clips can still contain errors.",
             "Metadata language hints are imperfect (the user found Hindi in English-labelled P9_41); their mismatch flags mean check the recording, not change its language.", "",
             "| Number | Clip | Review flags |", "|---:|---|---|"]
    lines.extend(f"| {r['number']} | {r['clip_id']} | {', '.join(r['flags'])} |" for r in records if r["flags"])
    (here / "A2_141_WHISPER_PASS_2_REVIEW.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
