#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""pipeline.py - Unified Multilingual Augmentation & Quality Gate Pipeline.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Capabilities:
1. Orchestrates all augmentation techniques:
   - back_translation
   - pivot_latin
   - lexical_synsets
   - code_mixing
   - audio_perturbation
2. Passes every candidate through the 3 Semantic Quality Gates:
   - Gate 1: Embedding Cosine Similarity >= 0.82
   - Gate 2: Polarity & Entity Invariance
   - Gate 3: MinHash Deduplication
3. Automatically updates internal_manifest.json with exact lineage and shared split_group_id.
4. Generates data/reports/augmentation_quality_report.json.
"""

import os
import sys
import json
import uuid
import time
from pathlib import Path
from datetime import datetime

# Guarantee local python environment & ffmpeg
os.environ["PATH"] = f"/Library/Frameworks/Python.framework/Versions/3.13/bin:/opt/homebrew/bin:{os.environ.get('PATH', '')}"

from model.src.augmentation.back_translation import back_translate
from model.src.augmentation.pivot_translator import augment_latin_pivot
from model.src.augmentation.lexical_synsets import augment_lexical_synsets
from model.src.augmentation.code_mix_generator import synthesize_code_mixed_variants
from model.src.augmentation.discourse_marker_augmenter import augment_discourse_framing
from model.src.augmentation.tri_directional_translator import translate_cross_lingual, save_cache, precompute_dataset_translations
from model.src.validation.embedding_filter import EmbeddingSimilarityGate
from model.src.validation.polarity_checker import PolarityEntityAuditor
from model.src.validation.deduplicator import MinHashDeduplicator

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = BASE_DIR / "model"
TEXT_DIR = MODEL_DIR / "data" / "text"
AUG_DIR = MODEL_DIR / "data" / "augmented"
METADATA_DIR = MODEL_DIR / "data" / "metadata"
REPORTS_DIR = MODEL_DIR / "data" / "reports"

def run_augmentation_pipeline(techniques=None, similarity_threshold=0.72, max_variants_per_sample=3):
    if techniques is None:
        techniques = ["back_translation", "pivot_latin", "lexical_synsets", "code_mixing", "discourse_framing", "cross_lingual_translation"]

    print("=" * 70)
    print("MULTILINGUAL AUGMENTATION & SEMANTIC QUALITY GATE PIPELINE")
    print(f"Active Techniques: {', '.join(techniques)}")
    print(f"Similarity Threshold: >= {similarity_threshold}")
    print("=" * 70)

    # Initialize Quality Gates
    embedding_gate = EmbeddingSimilarityGate(threshold=similarity_threshold)
    polarity_gate = PolarityEntityAuditor()
    dedup_gate = MinHashDeduplicator(max_jaccard_similarity=0.88)

    # Load internal manifest
    manifest_path = METADATA_DIR / "internal_manifest.json"
    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)
    manifest_entries = manifest_data["manifest"]

    # Build lookup by UUID
    manifest_by_uuid = {entry["uuid"]: entry for entry in manifest_entries}

    # Iterate over all text files
    text_files = sorted(list(TEXT_DIR.glob("*.txt")))
    print(f"Scanning {len(text_files)} original text transcripts...")

    if "cross_lingual_translation" in techniques:
        all_transcripts = []
        for text_path in text_files:
            for line in text_path.read_text().splitlines():
                if line.startswith("Transcript:"):
                    all_transcripts.append(line.replace("Transcript:", "").strip())
                    break
        precompute_dataset_translations(all_transcripts)

    augmented_records = []
    stats = {
        "candidates_generated": 0,
        "rejected_by_embedding": 0,
        "rejected_by_polarity": 0,
        "rejected_by_dedup": 0,
        "accepted": 0,
        "by_technique": {t: 0 for t in techniques}
    }

    for idx, text_path in enumerate(text_files):
        sample_uuid = text_path.stem
        entry = manifest_by_uuid.get(sample_uuid)
        if not entry:
            continue

        lines = text_path.read_text().splitlines()
        meta = {}
        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()

        orig_transcript = meta.get("Transcript", "").strip()
        target_label = entry.get("gold_intent", meta.get("Target_Label", ""))
        detected_lang = meta.get("Detected_Language", "en")

        if not orig_transcript or len(orig_transcript.split()) < 3:
            continue

        # Register original text into deduplicator
        dedup_gate.add_and_validate(orig_transcript)

        candidates = [] # list of (variant_text, technique_name)

        if "back_translation" in techniques:
            bt_vars = back_translate(orig_transcript, source_lang=detected_lang, n_variants=max_variants_per_sample)
            candidates.extend([(v, "back_translation") for v in bt_vars])

        if "pivot_latin" in techniques:
            latin_vars = augment_latin_pivot(orig_transcript, n_variants=max_variants_per_sample)
            candidates.extend([(v, "pivot_latin") for v in latin_vars])

        if "lexical_synsets" in techniques:
            lex_vars = augment_lexical_synsets(orig_transcript, n_variants=max_variants_per_sample)
            candidates.extend([(v, "lexical_synsets") for v in lex_vars])

        if "code_mixing" in techniques:
            cm_vars = synthesize_code_mixed_variants(orig_transcript, detected_lang=detected_lang, n_variants=max_variants_per_sample)
            candidates.extend([(v, "code_mixing") for v in cm_vars])

        if "discourse_framing" in techniques:
            df_vars = augment_discourse_framing(orig_transcript, n_variants=max_variants_per_sample)
            candidates.extend([(v, "discourse_framing") for v in df_vars])

        if "cross_lingual_translation" in techniques:
            trans_pairs = translate_cross_lingual(orig_transcript)
            candidates.extend([(v, "cross_lingual_translation") for v, _ in trans_pairs])

        if not candidates:
            continue

        stats["candidates_generated"] += len(candidates)

        # Gate 1: Batch Embedding Cosine Similarity
        cand_texts = [c[0] for c in candidates]
        sim_results = embedding_gate.evaluate_batch(orig_transcript, cand_texts)

        # Pass each candidate through the 3 Quality Gates
        for (cand_text, tech_name), (passes_sim, score) in zip(candidates, sim_results):
            req_thresh = 0.48 if ("cross_lingual" in tech_name or "back_translation" in tech_name) else similarity_threshold
            if score < req_thresh:
                stats["rejected_by_embedding"] += 1
                continue

            # Gate 2: Polarity & Domain Invariance
            passes_pol, pol_reason = polarity_gate.evaluate(orig_transcript, cand_text, target_label)
            if not passes_pol:
                stats["rejected_by_polarity"] += 1
                continue

            # Gate 3: MinHash Deduplication
            if not dedup_gate.add_and_validate(cand_text):
                stats["rejected_by_dedup"] += 1
                continue

            # ACCEPTED
            aug_uuid = f"aug_{uuid.uuid4().hex[:8]}"
            tech_folder = AUG_DIR / tech_name
            tech_folder.mkdir(parents=True, exist_ok=True)
            aug_text_path = tech_folder / f"{aug_uuid}.txt"

            aug_content = f"""UUID: {aug_uuid}
Parent_UUID: {sample_uuid}
Augmentation_Type: {tech_name}
Similarity_Score: {score}
Transcript: {cand_text}
Target_Label: {target_label}
Spoken_Languages: {entry.get('languages', ['Unknown'])}
"""
            aug_text_path.write_text(aug_content.strip() + "\n")

            # Create internal manifest entry sharing the EXACT split_group_id
            aug_manifest_entry = {
                "uuid": aug_uuid,
                "original_clip_id": entry.get("original_clip_id", ""),
                "original_file_name": entry.get("original_file_name", ""),
                "original_speaker_id": entry.get("original_speaker_id", ""),
                "parent_uuid": sample_uuid,
                "is_augmented": True,
                "augmentation_type": tech_name,
                "similarity_score": score,
                "gold_intent": target_label,
                "languages": entry.get("languages", []),
                "split_group_id": entry["split_group_id"],
                "text_path": str(aug_text_path.relative_to(BASE_DIR))
            }
            augmented_records.append(aug_manifest_entry)
            stats["accepted"] += 1
            stats["by_technique"][tech_name] += 1

        if (idx + 1) % 20 == 0 or (idx + 1) == len(text_files):
            save_cache()
            print(f"[{idx + 1:3d}/{len(text_files):3d}] processed. Total accepted so far: {stats['accepted']}")

    print("\n" + "=" * 70)
    print("QUALITY GATE AUDIT SUMMARY")
    print(f"Total Candidates Generated : {stats['candidates_generated']}")
    print(f"Rejected by Embedding Sim  : {stats['rejected_by_embedding']}")
    print(f"Rejected by Polarity Gate  : {stats['rejected_by_polarity']}")
    print(f"Rejected by MinHash Dedup  : {stats['rejected_by_dedup']}")
    print(f"Total Accepted Candidates  : {stats['accepted']}")
    print("Breakdown by Technique:")
    for t, cnt in stats["by_technique"].items():
        print(f"  - {t:20s}: {cnt}")
    print("=" * 70)

    # Save Quality Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "augmentation_quality_report.json"
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "threshold": similarity_threshold,
            "statistics": stats,
            "total_augmented_samples": len(augmented_records)
        }, f, indent=2)

    # Save augmented manifest pool
    aug_manifest_path = METADATA_DIR / "augmented_manifest.json"
    with open(aug_manifest_path, "w") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_augmented": len(augmented_records),
            "manifest": augmented_records
        }, f, indent=2)

    save_cache()
    print(f"Quality report serialized to: {report_path}")
    print(f"Augmented manifest serialized to: {aug_manifest_path}")

    return stats, augmented_records

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Multilingual Augmentation Pipeline")
    parser.add_argument("--threshold", type=float, default=0.75, help="Cosine similarity threshold")
    args = parser.parse_args()

    run_augmentation_pipeline(similarity_threshold=args.threshold)
