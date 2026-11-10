#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""evaluate_asr.py - Offline ASR Evaluation and Matching Metric Engine.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Calculates:
1. Word Error Rate (WER) via Levenshtein edit distance on word tokens.
2. Character Error Rate (CER) via Levenshtein edit distance on unicode characters.
3. Lexical Match / Similarity Score between ASR hypothesis and gold ground truth.
4. Stratified breakdowns across:
   - Language slices (English, Hindi, Gujarati, Code-Mixed)
   - Intent slices (admissions, hostel_mess, it_support, student_services)
5. Serializes formatted report to model/data/reports/asr_evaluation_report.json.
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = BASE_DIR / "model"
TEXT_DIR = MODEL_DIR / "data" / "text"
METADATA_DIR = MODEL_DIR / "data" / "metadata"
REPORTS_DIR = MODEL_DIR / "data" / "reports"

def normalize_text(text: str) -> str:
    """Standardizes text for robust fair metric computation."""
    if not text:
        return ""
    text = text.lower()
    # Remove punctuation
    text = re.sub(r"[^\w\s\u0900-\u097F\u0A80-\u0AFF]", " ", text)
    # Collapse multiple whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def levenshtein_distance(seq1, seq2):
    """Computes standard dynamic programming Levenshtein distance."""
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = [[0] * size_y for _ in range(size_x)]

    for x in range(size_x):
        matrix[x][0] = x
    for y in range(size_y):
        matrix[0][y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x - 1] == seq2[y - 1]:
                matrix[x][y] = matrix[x - 1][y - 1]
            else:
                matrix[x][y] = min(
                    matrix[x - 1][y] + 1,       # Deletion
                    matrix[x][y - 1] + 1,       # Insertion
                    matrix[x - 1][y - 1] + 1    # Substitution
                )
    return matrix[size_x - 1][size_y - 1]

def compute_wer_cer(ref_text: str, hyp_text: str):
    ref_norm = normalize_text(ref_text)
    hyp_norm = normalize_text(hyp_text)

    # Word Error Rate
    ref_words = ref_norm.split()
    hyp_words = hyp_norm.split()

    if len(ref_words) == 0:
        wer = 1.0 if len(hyp_words) > 0 else 0.0
    else:
        dist_w = levenshtein_distance(ref_words, hyp_words)
        wer = dist_w / len(ref_words)

    # Character Error Rate
    ref_chars = list(ref_norm.replace(" ", ""))
    hyp_chars = list(hyp_norm.replace(" ", ""))

    if len(ref_chars) == 0:
        cer = 1.0 if len(hyp_chars) > 0 else 0.0
    else:
        dist_c = levenshtein_distance(ref_chars, hyp_chars)
        cer = dist_c / len(ref_chars)

    # Lexical Match Score (Jaccard similarity on word set)
    set_r = set(ref_words)
    set_h = set(hyp_words)
    if not set_r and not set_h:
        match_score = 1.0
    elif not set_r or not set_h:
        match_score = 0.0
    else:
        match_score = len(set_r & set_h) / len(set_r | set_h)

    return wer, cer, match_score

def evaluate_asr_engine():
    print("=" * 70)
    print("OFFLINE ASR BENCHMARK & METRIC EVALUATION ENGINE")
    print("=" * 70)

    preds_file = REPORTS_DIR / "offline_asr_predictions.json"
    if not preds_file.exists():
        raise FileNotFoundError(f"Predictions file not found at {preds_file}. Run transcribe.py first.")

    with open(preds_file, "r", encoding="utf-8") as f:
        preds_data = json.load(f)
    predictions = preds_data["predictions"]

    gold_manifest_file = METADATA_DIR / "gold_transcripts_manifest.json"
    gold_map = {}
    if gold_manifest_file.exists():
        with open(gold_manifest_file, "r", encoding="utf-8") as f:
            gold_data = json.load(f)
            gold_map = {item["uuid"]: item for item in gold_data["manifest"]}

    eval_items = []
    total_wer = 0.0
    total_cer = 0.0
    total_match = 0.0

    by_lang = defaultdict(lambda: {"wer": [], "cer": [], "match": []})
    by_intent = defaultdict(lambda: {"wer": [], "cer": [], "match": []})

    for p in predictions:
        u = p["uuid"]
        hyp_text = p.get("transcription", "")
        
        # Resolve reference text
        if u in gold_map:
            ref_text = gold_map[u]["transcript"]
            gold_intent = gold_map[u]["gold_intent"]
            langs = gold_map[u].get("languages", ["English"])
        else:
            txt_file = TEXT_DIR / f"{u}.txt"
            ref_text = ""
            gold_intent = p.get("gold_intent", "")
            langs = p.get("languages", ["English"])
            if txt_file.exists():
                for line in txt_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("Transcript:"):
                        ref_text = line.replace("Transcript:", "").strip()

        wer, cer, match = compute_wer_cer(ref_text, hyp_text)
        
        total_wer += wer
        total_cer += cer
        total_match += match

        # Language categorization
        if len(langs) > 1:
            lang_cat = "Code-Mixed"
        else:
            lang_cat = langs[0] if langs else "English"

        by_lang[lang_cat]["wer"].append(wer)
        by_lang[lang_cat]["cer"].append(cer)
        by_lang[lang_cat]["match"].append(match)

        by_intent[gold_intent]["wer"].append(wer)
        by_intent[gold_intent]["cer"].append(cer)
        by_intent[gold_intent]["match"].append(match)

        eval_items.append({
            "uuid": u,
            "gold_intent": gold_intent,
            "language_category": lang_cat,
            "gold_transcript": ref_text,
            "asr_prediction": hyp_text,
            "wer": round(wer, 4),
            "cer": round(cer, 4),
            "match_score": round(match, 4),
            "rtf": p.get("rtf", 0.0)
        })

    n = len(eval_items)
    avg_wer = total_wer / n if n > 0 else 0.0
    avg_cer = total_cer / n if n > 0 else 0.0
    avg_match = total_match / n if n > 0 else 0.0

    # Aggregate by language
    lang_summary = {}
    for lcat, data in by_lang.items():
        k = len(data["wer"])
        lang_summary[lcat] = {
            "samples": k,
            "mean_wer": round(sum(data["wer"]) / k, 4),
            "mean_cer": round(sum(data["cer"]) / k, 4),
            "mean_match": round(sum(data["match"]) / k, 4)
        }

    # Aggregate by intent
    intent_summary = {}
    for icat, data in by_intent.items():
        k = len(data["wer"])
        intent_summary[icat] = {
            "samples": k,
            "mean_wer": round(sum(data["wer"]) / k, 4),
            "mean_cer": round(sum(data["cer"]) / k, 4),
            "mean_match": round(sum(data["match"]) / k, 4)
        }

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_evaluated_clips": n,
        "corpus_averages": {
            "mean_wer": round(avg_wer, 4),
            "mean_cer": round(avg_cer, 4),
            "mean_match_score": round(avg_match, 4),
            "overall_rtf": preds_data.get("overall_rtf", 0.0)
        },
        "language_slice_breakdown": lang_summary,
        "intent_slice_breakdown": intent_summary,
        "clip_evaluations": eval_items
    }

    report_path = REPORTS_DIR / "asr_evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("ASR EVALUATION RESULTS SUMMARY")
    print("=" * 70)
    print(f"Total Evaluated Clips : {n}")
    print(f"Mean Word Error Rate  : {avg_wer:.4f} ({avg_wer * 100:.1f}%)")
    print(f"Mean Char Error Rate  : {avg_cer:.4f} ({avg_cer * 100:.1f}%)")
    print(f"Mean Match Similarity : {avg_match:.4f} ({avg_match * 100:.1f}%)")
    print(f"Real-Time Factor (RTF): {preds_data.get('overall_rtf', 0.0):.3f}")
    
    print("\n--- By Spoken Language Slice ---")
    print(f"{'Language':<15} | {'Clips':<6} | {'Mean WER':<10} | {'Mean CER':<10} | {'Match Score':<12}")
    print("-" * 62)
    for lcat, s in sorted(lang_summary.items()):
        print(f"{lcat:<15} | {s['samples']:<6d} | {s['mean_wer']:<10.4f} | {s['mean_cer']:<10.4f} | {s['mean_match']:<12.4f}")

    print("\n--- By Intent Category Slice ---")
    print(f"{'Intent':<18} | {'Clips':<6} | {'Mean WER':<10} | {'Mean CER':<10} | {'Match Score':<12}")
    print("-" * 62)
    for icat, s in sorted(intent_summary.items()):
        print(f"{icat:<18} | {s['samples']:<6d} | {s['mean_wer']:<10.4f} | {s['mean_cer']:<10.4f} | {s['mean_match']:<12.4f}")

    print("\n" + "=" * 70)
    print(f"Detailed ASR report written to: {report_path}")
    print("=" * 70)
    return report_path

if __name__ == "__main__":
    evaluate_asr_engine()

