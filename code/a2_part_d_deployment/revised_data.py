"""Load the revised release split and stage the audio needed by the image."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import wave


ROOT = Path(__file__).resolve().parents[2]
CLASSES = {"admissions", "hostel_mess", "it_support", "student_services"}


def load_json(relative_path, root=ROOT):
    return json.loads((root / relative_path).read_text(encoding="utf-8-sig"))


def release_rows(root=ROOT):
    consensus = load_json("final_annotation/consensus_gold_182.json", root)["clips"]
    annotations = {row["clip_id"]: row for row in consensus}
    # Reference transcripts come ONLY from the human transcription round (Round T). The curated
    # strings in gold_transcripts_manifest.json were withdrawn (model/results/reference_audit.json).
    references = {}
    human = root / "data/labels/human_transcripts.csv"
    if human.exists():
        with human.open(encoding="utf-8", newline="") as stream:
            references = {row["uuid"]: row["transcript"] for row in csv.DictReader(stream)}
    asr = {row["uuid"]: row["transcription"]
           for row in load_json("model/data/reports/offline_asr_predictions.json", root)["predictions"]}
    splits = load_json("model/data/splits/release_speakers.json", root)
    validation, test = set(splits["validation"]), set(splits["test"])
    if validation & test or {"P15", "P17", "P18", "P19"} & validation:
        raise ValueError("Release speaker partitions overlap")

    metadata = root / "model/data/metadata/metadata_182.csv"
    with metadata.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != len(annotations) or len(rows) != len(asr):
        raise ValueError("Release metadata and annotation counts differ")
    for field in ("uuid", "original_clip_id", "sha256"):
        if len({row[field] for row in rows}) != len(rows):
            raise ValueError(f"Release metadata contains duplicate {field}")

    groups = {"train": [], "validation": [], "test": []}
    for row in rows:
        uuid, speaker, clip = (row[key] for key in ("uuid", "original_speaker_id", "original_clip_id"))
        if row["audio_path"] != f"model/data/audio/{uuid}.wav" or Path(uuid).name != uuid:
            raise ValueError(f"Unexpected audio path for {uuid}")
        annotation = annotations[clip]
        if annotation["speaker_id"] != speaker:
            raise ValueError(f"Speaker mismatch for {uuid}")
        if speaker in test:
            partition = "test"
        elif speaker in validation:
            partition = "validation"
        else:
            if speaker in {"P15", "P17", "P18", "P19"}:
                raise ValueError(f"Pilot gold speaker {speaker} may not train the release router")
            partition = "train"
        groups[partition].append({**row, "intent": annotation["gold_intent"], "a1": annotation["a1_intent"],
                                  "a2": annotation["a2_intent"], "languages": annotation["languages"],
                                  "text": asr[uuid], "reference": references.get(uuid)})
    for partition, items in groups.items():
        if {row["intent"] for row in items} != CLASSES:
            raise ValueError(f"Release {partition} does not cover the four intents")
    return groups


def examples(groups):
    return [min((row for row in groups["validation"] if row["intent"] == intent),
                key=lambda row: (float(row["duration_sec"]), row["uuid"])) for intent in sorted(CLASSES)]


def check_wav(audio):
    with wave.open(str(audio), "rb") as stream:
        if (stream.getnchannels(), stream.getframerate(), stream.getsampwidth()) != (1, 16000, 2):
            raise ValueError(f"Expected 16 kHz mono PCM16 WAV: {audio.name}")
        frames = stream.getnframes()
        if not frames or len(stream.readframes(frames)) != frames * 2:
            raise ValueError(f"Empty or truncated WAV: {audio.name}")
    return frames / 16000


def check_sample(audio, row):
    if hashlib.sha256(audio.read_bytes()).hexdigest() != row["sha256"]:
        raise ValueError(f"SHA-256 mismatch: {audio.name}")
    duration = check_wav(audio)
    if abs(duration - float(row["duration_sec"])) > 0.02:
        raise ValueError(f"Duration mismatch: {audio.name}")
    return duration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="WAV directory restored by DVC")
    parser.add_argument("output", type=Path, help="New staging directory outside the Git checkout")
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(ROOT):
        parser.error("stage the release audio outside the Git checkout")
    groups = release_rows()
    selected = groups["test"] + examples(groups)
    for row in selected:
        check_sample(args.source / f"{row['uuid']}.wav", row)
    args.output.mkdir(parents=True, exist_ok=False)
    for row in selected:
        name = f"{row['uuid']}.wav"
        shutil.copyfile(args.source / name, args.output / name)
    print(f"Staged {len(groups['test'])} test WAVs and {len(examples(groups))} validation examples")


if __name__ == "__main__":
    main()
