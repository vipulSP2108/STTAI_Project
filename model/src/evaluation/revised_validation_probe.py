"""Compare release accuracy on validation without evaluating either test set.

Run inside the revised Docker image with its deployment module directory on
PYTHONPATH. Mount the DVC WAV directory and teammate ZIP read-only for live ASR.
"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from faster_whisper import WhisperModel
import jiwer
import joblib
from scipy.stats import binomtest
from sklearn.base import clone
from sklearn.metrics import f1_score

from revised_data import CLASSES, check_sample, release_rows
from revised_release import ASR_PATH, ROUTER_PATH, normalise, version


def score(rows, text, router):
    refs = [normalise(row["reference"]) for row in rows]
    hypotheses = [normalise(line) for line in text]
    gold = [row["intent"] for row in rows]
    predicted = [str(intent) if line else "" for intent, line in zip(router.predict(hypotheses), hypotheses)]
    correct = [label == intent for label, intent in zip(gold, predicted)]
    words = jiwer.process_words(refs, hypotheses)
    return {
        "clips": len(rows),
        "correct": sum(correct),
        "intent_accuracy": sum(correct) / len(rows),
        "intent_macro_f1": f1_score(gold, predicted, labels=sorted(CLASSES), average="macro", zero_division=0),
        "wer": words.wer,
        "cer": jiwer.cer(refs, hypotheses),
        "word_insertions": words.insertions,
        "word_deletions": words.deletions,
        "word_substitutions": words.substitutions,
        "empty_hypotheses": hypotheses.count(""),
    }, correct


def paired(before, after):
    wins = sum(not a and b for a, b in zip(before, after))
    losses = sum(a and not b for a, b in zip(before, after))
    return {"wins": wins, "losses": losses,
            "mcnemar_exact_p": binomtest(wins, wins + losses).pvalue if wins + losses else 1.0}


def load_archived_models(archive, work):
    base_vocab = (ASR_PATH / "vocabulary.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    with ZipFile(archive) as bundle:
        for code, language in (("hi", "hindi"), ("gu", "gujarati")):
            name = f"whisper-{language}-ct2"
            prefix = f"STTAI_Project/model/models/{name}/"
            vocab = json.loads(bundle.read(prefix + "vocabulary.json"))
            differences = [(a, b) for a, b in zip(vocab, base_vocab) if a != b]
            # The Hebrew language token uses its old spelling at the same ID.
            # These checkpoints are only invoked with an explicit Hindi or Gujarati token.
            if len(vocab) != len(base_vocab) or differences not in ([], [("<|iw|>", "<|he|>")]):
                raise ValueError(f"Archived {language} vocabulary differs from the bundled tokenizer")
            model = work / name
            model.mkdir()
            for file in ("config.json", "vocabulary.json", "model.bin"):
                with bundle.open(prefix + file) as source, (model / file).open("xb") as target:
                    shutil.copyfileobj(source, target)
            shutil.copyfile(ASR_PATH / "tokenizer.json", model / "tokenizer.json")
            yield code, load_asr(model)


def load_asr(path, workers=1):
    return WhisperModel(str(path), device="cpu", compute_type="int8", cpu_threads=2,
                        num_workers=workers, local_files_only=True)


def transcribe(model, audio, **settings):
    segments, info = model.transcribe(str(audio), beam_size=1, condition_on_previous_text=False, **settings)
    return " ".join(segment.text.strip() for segment in segments).strip(), info.language


def compare_live(rows, audio_dir, archive, current_router, mixed_router):
    for row in rows:
        check_sample(audio_dir / f"{row['uuid']}.wav", row)
    audio_paths = [audio_dir / f"{row['uuid']}.wav" for row in rows]
    base = load_asr(ASR_PATH, workers=2)

    def decode(audio):
        baseline, language = transcribe(base, audio)
        vad, _ = transcribe(base, audio, vad_filter=True)
        return baseline, vad, language

    with ThreadPoolExecutor(max_workers=2) as workers:
        outputs = []
        for output in workers.map(decode, audio_paths):
            outputs.append(output)
            print(f"Base and VAD completed on clip {len(outputs)}/{len(rows)}", flush=True)
    del base

    baseline, vad, languages = zip(*outputs)
    routed = list(baseline)
    specialized = []
    if archive:
        with TemporaryDirectory() as directory:
            for code, model in load_archived_models(archive, Path(directory)):
                for index, language in enumerate(languages):
                    if language == code:
                        routed[index], _ = transcribe(model, audio_paths[index], language=code, vad_filter=True)
                specialized.append(code)
                print(f"Archived {code} model completed on {languages.count(code)} clips", flush=True)
                del model

    results = {"detected_languages": dict(Counter(languages)), "specialized_models_loaded": sorted(specialized)}
    results["base"], control = score(rows, baseline, current_router)
    options = {"base_mixed_router": (baseline, mixed_router), "base_vad": (vad, current_router),
               "base_vad_mixed_router": (vad, mixed_router)}
    if specialized:
        options.update({"language_routed": (routed, current_router),
                        "language_routed_mixed_router": (routed, mixed_router)})
    for name, (text, router) in options.items():
        results[name], correctness = score(rows, text, router)
        results[name]["paired_vs_base"] = paired(control, correctness)
    return results


def screening_rows(validation):
    selected = []
    for language in sorted({row["languages"] for row in validation}):
        rows = sorted((row for row in validation if row["languages"] == language),
                      key=lambda row: (float(row["duration_sec"]), row["uuid"]))
        selected.extend(rows if len(rows) <= 3 else [rows[0], rows[len(rows) // 2], rows[-1]])
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--audio-dir", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--screen", action="store_true", help="Use a deterministic length/language sample for live ASR")
    args = parser.parse_args()
    groups = release_rows()
    train, validation = groups["train"], groups["validation"]
    archive_cache = json.loads(args.cache.read_text(encoding="utf-8"))["predictions"]
    allowed = {row["uuid"] for row in train + validation}
    cached = {row["uuid"]: row["transcription"] for row in archive_cache if row["uuid"] in allowed}
    cached = {uuid: "" if text.startswith("[TRANSCRIPTION_ERROR:") else text for uuid, text in cached.items()}
    current = joblib.load(ROUTER_PATH)
    mixed = clone(current)
    training_pairs = [(normalise(text), row["intent"]) for row in train
                      for text in (row["reference"], cached[row["uuid"]]) if normalise(text)]
    x, y = zip(*training_pairs)
    mixed.fit(x, y)
    reference_text = [row["reference"] for row in validation]
    cached_text = [cached[row["uuid"]] for row in validation]
    payload = {
        **version(),
        "split": "revised_release_validation",
        "training_clips": len(train),
        "validation_clips": len(validation),
        "validation_languages": dict(Counter(row["languages"] for row in validation)),
        "reference_text_current_router": score(validation, reference_text, current)[0],
        "archived_label_guided_asr_current_router": score(validation, cached_text, current)[0],
        "archived_label_guided_asr_mixed_router": score(validation, cached_text, mixed)[0],
    }
    print(json.dumps(payload, indent=2), flush=True)
    if args.audio_dir:
        live_rows = screening_rows(validation) if args.screen else validation
        payload["live_selection"] = "shortest, median, and longest per language tag" if args.screen else "all validation"
        payload["live_uuids"] = [row["uuid"] for row in live_rows]
        payload["live"] = compare_live(live_rows, args.audio_dir, args.archive, current, mixed)
        print(json.dumps(payload["live"], indent=2), flush=True)
    if args.output:
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
