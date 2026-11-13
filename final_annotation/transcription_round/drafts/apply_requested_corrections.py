"""Apply requested IIT GN edits and audio-supported U+FFFD repairs; retain raw ASR."""
import hashlib
import json
from pathlib import Path
import re
from normalize_iitgn import normalize

HERE = Path(__file__).resolve().parent
FIXES = {
    2: {47: ""},
    9: {26: "", 61: "મળે છે? શું હોસ્ટેલમાં રહેતા વિદ્યાર્થીઓને medical", 65: "", 93: "", 96: ""},
    14: {124: "यू"},
    15: {26: "જરૂરી છે. IIT GNમાં હોસ્ટેલની", 36: "હોય છે", 42: "મેસનો", 81: "", 90: "શકાય? જો દર વર્ષે ફીમાં ફેરફાર થતો", 98: ""},
    17: {64: "लोड"}, 18: {20: "student status certificate"}, 19: {20: "application"},
    21: {25: "मदद करें"}, 22: {5: "ગાંધીનગર", 43: "કે", 53: "ટેબલ", 73: "અરજી", 83: "કરવી"},
    28: {182: "", 210: ""},
    31: {37: "તેને", 54: "લેવાના", 64: "દીકરીને મળવા આવે ત્યારે કોઈ નક્કી કરેલી", 104: "રોકાવાની સુવિધા મળે છે કે પછી બહાર", 110: "કૃપા", 117: "અગાઉથી"},
    33: {6: ""}, 46: {14: "accommodation"}, 50: {117: "ध्यान कर दें"}, 51: {22: ""},
    63: {99: "I would appreciate"}, 64: {140: "हुआ"}, 68: {80: "please"}, 70: {24: "लेकिन"},
    72: {13: "night"}, 77: {11: "plagiarism limit"}, 82: {15: ""}, 85: {17: ""}, 87: {23: "हुआ"},
    92: {18: "application कैसे करते हैं"}, 93: {15: "urgent"},
    97: {29: "branch", 61: "fee", 73: "upgrade કરવાનો વિકલ્પ મળે છે.", 78: "રીતે તપાસવું અને સંસ્થા તરફથી", 81: "નિયમિત રીતે જોવાનું કેટલું જરૂરી છે તે પણ", 84: "છું. અમે કોઈ મહત્વની તારીખ ચૂકી જવા", 88: "counselling"},
    101: {13: "vegetarian"}, 103: {25: "વિશે", 46: "", 116: "મેળવવાની"}, 113: {52: ""},
    116: {16: "update"}, 135: {19: "renew"},
    136: {23: "પહેલી", 39: "પીવાનું સ્વચ્છ પાણી, ગરમ પાણી, કપડાં ધોવાની અને રૂમની સફાઈની સુવિધાઓ", 101: "મુશ્કેલી ન પડે", 116: "સુવિધાઓ"},
    139: {17: ""},
}
SPANS = {
    19: [("application क्वेश्चन", "application")],
    63: [("I would appreciate left it if you could also", "I would appreciate it if you could also")],
    103: [("વિશે સે", "વિશે"), ("મેળવવાની मेडवान", "મેળવવાની")],
    136: [("પહેલી पहली", "પહેલી"), ("મુશ્કેલી ન પડે No, put it.", "મુશ્કેલી ન પડે")],
    139: [("लाइक Thank वह", "लाइक वह")],
}


def counts(text):
    return {"latin": len(re.findall(r"[A-Za-z]", text)), "devanagari": len(re.findall(r"[\u0900-\u097f]", text)),
            "gujarati": len(re.findall(r"[\u0a80-\u0aff]", text)), "arabic": len(re.findall(r"[\u0600-\u06ff]", text))}


def main():
    raw_file = HERE / "raw_backup/A2_141_WHISPER_PASS_2.json"
    data = json.loads(raw_file.read_text(encoding="utf-8"))
    candidates = json.loads((HERE / "character_repair_candidates.json").read_text(encoding="utf-8"))["regions"]
    log = []
    for row in data["transcripts"]:
        original = row["transcript"]
        fragments = [w["word"] for w in row["words"]]
        if "".join(fragments).strip() != original:
            raise RuntimeError("Raw word/text mismatch")
        edits = []
        mapping = FIXES.get(row["number"], {})
        bad_indices = {i for i, word in enumerate(fragments) if "\ufffd" in word}
        if bad_indices != set(mapping):
            raise RuntimeError(f"Repair plan does not cover damaged words: {row['number']}")
        for index, replacement in mapping.items():
            old = fragments[index]
            evidence = [{"start": c["start"], "end": c["end"], "language_hint": c["language_hint"]}
                        for c in candidates if c["number"] == row["number"] and index in c["damaged_word_indices"]]
            if not evidence:
                raise RuntimeError("Missing audio repair evidence")
            fragments[index] = " " + replacement if replacement else ""
            edits.append({"kind": "audio_assisted_character_repair", "word_index": index, "before": old,
                          "after": replacement, "evidence": evidence})
        text = "".join(fragments).strip()
        for old, new in SPANS.get(row["number"], []):
            if old in text:
                text = text.replace(old, new)
                edits.append({"kind": "audio_assisted_fragment_join", "before": old, "after": new})
        text, entity_edits = normalize(text)
        edits.extend(entity_edits)
        if "\ufffd" in text:
            raise RuntimeError("Unrepaired replacement character")
        if re.search(r"\biit\s+jain\b", text, re.I):
            raise RuntimeError("Unrepaired IIT Jain")
        if edits or text != original:
            row["raw_transcript"] = original
            row["raw_script_counts"] = row["script_counts"]
            row["transcript"] = text
            row["script_counts"] = counts(text)
            row["post_edits"] = edits
            row["post_edit_status"] = "user_requested_entity_and_character_repairs"
            log.append({"number": row["number"], "clip_id": row["clip_id"], "edits": edits})
    data["description"] = "ASR drafts with user-requested IIT GN normalization and audio-assisted damaged-character repairs. Raw words/chunks and backups retain original model output; not human-verified."
    data["editorial_corrections"] = {"raw_source_sha256": hashlib.sha256(raw_file.read_bytes()).hexdigest(),
                                    "edited_clips": len(log), "damaged_words_repaired": sum(len(x) for x in FIXES.values()),
                                    "entity_edits": sum(e["kind"] == "user_requested_entity_normalization" for r in log for e in r["edits"]),
                                    "repair_candidates": "character_repair_candidates.json", "focused_candidates": "character_repair_focused.json"}
    target = HERE / "A2_141_WHISPER_PASS_2.json"
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(target)
    lines = ["A2 — 141 TRANSCRIPTS WITH IIT GN AND CHARACTER CORRECTIONS", "",
             "ASR drafts with requested entity normalization and audio-assisted character repairs; not human-verified.",
             "English/Hindi/Gujarati text is preserved. Original raw decoding is backed up separately.", ""]
    for row in data["transcripts"]:
        lines.extend(["="*76, f"{row['number']:03d}/141 | {row['clip_id']} | {row['uuid']}", "", row["transcript"], ""])
    (HERE / "A2_141_WHISPER_PASS_2.txt").write_text("\n".join(lines), encoding="utf-8-sig")
    (HERE / "requested_corrections_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data["editorial_corrections"], indent=2))


if __name__ == "__main__":
    main()
