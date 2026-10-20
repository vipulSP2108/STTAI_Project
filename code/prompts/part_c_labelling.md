# Prompts Used — Part C: Labelling and Agreement
<!-- Required by CS203 Assignment 1 Grader AI -->

## Prompt 1: Inter-Annotator Agreement & Gold Test Set Freeze
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-18  
**Output file**: `code/part_c_labelling/compute_agreement.py`  

**Exact prompt**:
"""
Build `part_c_labelling/compute_agreement.py` that:

1. Reads TWO Label Studio JSON exports:
   supporting_files/label_studio_exports/round1_annotator_a.json
   supporting_files/label_studio_exports/round1_annotator_b.json
2. TRANSCRIPT agreement (WER):
   - Use jiwer: from jiwer import wer
   - For each clip in the overlap set: compute wer(ref=annotator_a, hyp=annotator_b)
   - Report: mean WER, median WER, std WER
   - Print worst 10 clips (highest WER) with clip_id and both transcripts
3. INTENT agreement (Cohen's kappa):
   - Use sklearn.metrics.cohen_kappa_score
   - Print the 4x4 confusion matrix (admissions/hostel_mess/it_support/student_services)
   - Print the 10 clips where annotators disagreed on intent, with clip_id + both labels
4. Run for ROUND 1 (v1 guidelines) and ROUND 2 (v2 guidelines) and compare:
   Before (v1): WER=X, Kappa=Y
   After  (v2): WER=A, Kappa=B   <- should show improvement
5. Save everything to:
   supporting_files/agreement_calculations/agreement_report.json
6. FREEZE gold test set:
   - Select clips where BOTH annotators agree exactly on transcript (WER=0) AND intent
   - Write to data/gold_test_set.csv
   - Print: "Gold test set frozen: N clips. NEVER use for tuning (A1 or A2)."

Add comment:
# ============================================================
# Part C: Inter-Annotator Agreement
# CS203 Assignment 1 — Project 5
# ============================================================
"""

**Notes**: Implemented pure Python Levenshtein fallback for WER calculation in environments without jiwer.

---

## Prompt 2: Label Studio Schema with Strict Level Hierarchy
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-18  
**Output file**: `code/part_c_labelling/label_studio_config.xml`  

**Exact prompt**:
"""
Write Label Studio config XML for Project 5 audio transcription + intent labelling:

Requirements:
- Audio player (plays the .wav clip)
- TextArea for transcript:
  placeholder="Type code-mixed transcript (English/हिन्दी/ગુજરાતી)"
  name="transcript"
- Choices for intent (single choice):
  name="intent"
  choices: admissions | hostel_mess | it_support | student_services

CRITICAL: The XML layout must force transcript before intent by putting
TextArea BEFORE Choices in the XML order.

Add XML comment:
<!-- LABEL ORDER: transcript -> intent
     Annotators MUST fill transcript first, then choose intent.
     This prevents intent choice from biasing the transcription.
     See LABELLING_PROTOCOL.md for the rationale. -->
"""

**Notes**: Configured zoom controls and space hotkey for audio playback.

---

## Prompt 3: Annotation Guidelines Formulation (v1 & v2)
**Model**: Claude Sonnet 3.5 / ChatGPT-4o  
**Date**: 2026-10-18  
**Output file**: `code/part_c_labelling/guidelines_v1.md`, `code/part_c_labelling/guidelines_v2.md`  

**Exact prompt**:
"""
Write annotation guidelines for code-mixed English-Hindi-Gujarati helpdesk speech:
1. Script rules: Devanagari for Hindi words, Gujarati script for Gujarati words, Latin for English.
2. Normalization: expand abbreviations, delete fillers (um, uh, hmm), standard tokens ([NOISE], [MUSIC], [UNK]).
3. Intent definitions: admissions, hostel_mess, it_support, student_services.
4. Worked examples with edge cases.
5. In v2, revise rules based on Round 1 disagreements (strictly omit 'haan'/'huh', Devanagari transliteration for Hindi loanwords, first-mention tiebreaker for multi-topic queries).
"""

**Notes**: Outlines the progression from v1 to v2 that pushed Cohen's kappa from 0.911 to 1.000.
