"""make_tasks.py - Build the Round T (transcription) task files for Label Studio.

* double_100.json : 100 clips stratified by language (and spread over speakers), labelled
                    independently by A1 and A2 with NO pre-annotation. Used for inter-annotator WER.
* single_A1/A2.json : the remaining 82 clips, one annotator each (41 + 41), pre-filled with the
                    Indic ASR draft (asr_indic_v2_confidence.json) for post-editing.
* Item order is shuffled with seed 2026 and written to order_manifest.json so the order shown to
  annotators is reproducible (A1 protocol requirement "order of items").

Usage: python final_annotation/transcription_round/make_tasks.py
"""
import json
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
FA = HERE.parent
SEED = 2026
N_DOUBLE = 100


def main():
    clips = json.loads((FA / "consensus_gold_182.json").read_text())["clips"]
    rng = random.Random(SEED)
    by_lang = defaultdict(list)
    for c in clips:
        lang = "Code-mixed" if len(c["languages"]) > 1 else c["languages"][0]
        by_lang[lang].append(c)
    # proportional allocation per language, round-robin over speakers inside a language
    double = []
    for lang, rows in sorted(by_lang.items()):
        k = round(N_DOUBLE * len(rows) / len(clips))
        by_spk = defaultdict(list)
        for r in rows:
            by_spk[r["speaker_id"]].append(r)
        for v in by_spk.values():
            rng.shuffle(v)
        pick, spk = [], sorted(by_spk)
        while len(pick) < k and any(by_spk.values()):
            for s in spk:
                if by_spk[s] and len(pick) < k:
                    pick.append(by_spk[s].pop())
        double.extend(pick)
    double = double[:N_DOUBLE]
    ids = {c["clip_id"] for c in double}
    single = [c for c in clips if c["clip_id"] not in ids]
    rng.shuffle(double); rng.shuffle(single)

    man = {m["original_clip_id"]: m["uuid"] for m in json.loads((FA.parent / "model/data/metadata/internal_manifest.json").read_text())["manifest"]}
    asr = {r["uuid"]: r["transcription"] for r in json.loads((FA.parent / "model/data/reports/asr_indic_v2_confidence.json").read_text())["clips"]}

    def task(c, draft=False):  # what the annotator sees: audio, a neutral id, and (single clips only) an ASR draft
        t = {"data": {"audio": c["audio"], "clip_id": c["clip_id"]}}
        if draft:
            t["predictions"] = [{"model_version": "indic-asr-v2", "result": [{
                "from_name": "transcript", "to_name": "audio", "type": "textarea",
                "value": {"text": [asr[man[c["clip_id"]]]]}}]}]
        return t

    (HERE / "double_100.json").write_text(json.dumps([task(c) for c in double], indent=1, ensure_ascii=False))
    half = len(single) // 2
    (HERE / "single_A1.json").write_text(json.dumps([task(c, True) for c in single[:half]], indent=1, ensure_ascii=False))
    (HERE / "single_A2.json").write_text(json.dumps([task(c, True) for c in single[half:]], indent=1, ensure_ascii=False))
    (HERE / "order_manifest.json").write_text(json.dumps({
        "seed": SEED,
        "double_100_order": [c["clip_id"] for c in double],
        "single_A1_order": [c["clip_id"] for c in single[:half]],
        "single_A2_order": [c["clip_id"] for c in single[half:]],
        "double_language_counts": {L: sum(1 for c in double if ("Code-mixed" if len(c["languages"]) > 1 else c["languages"][0]) == L)
                                   for L in sorted(by_lang)},
        "double_speakers": len({c["speaker_id"] for c in double}),
    }, indent=1))
    print(f"double {len(double)} | single A1 {half} | single A2 {len(single) - half}")


if __name__ == "__main__":
    main()
