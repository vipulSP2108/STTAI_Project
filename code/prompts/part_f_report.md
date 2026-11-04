# Prompts Used — Part F: Report, Deliverables, and Documentation
<!-- Required by CS203 Assignment 1 Grader AI -->

## Prompt 1: LaTeX Technical Report Generation
**Model**: Claude 3.5 Sonnet (Anthropic, build 20241022)  
**Date**: 2026-10-18  
**Output file**: `report/report.tex`  

**Exact prompt**:
"""
Write a rigorous, professional 6-page IEEE/ACM style technical report in LaTeX for CS203 Assignment 1 (Project 5: Cross-Lingual Institute Voice Helpdesk ASR with Drift-Triggered Retraining) at IIT Gandhinagar.

Authors:
- Rajdeep Vraj (23110260)
- Vipul Sunil Patil (23110370)
- Satvik Sharma (23110290)

The report must cover:
1. Executive Summary & Problem Formulation: Cross-lingual code-mixed (Hindi/Gujarati/English) institute voice helpdesk ASR and 4-way intent classification under acoustic and dialectal drift.
2. Dataset Collection & Demographics (Part A): 19 participants, 249 canonical WAV clips (1.29 hours raw / 1.255 hours segmented audio), 19 phone models, 5 noise environments on IITGN campus. Note that A1 establishes the 19-speaker benchmark with pipeline architected to scale to 30+ speakers / 2.0+ hours for the course final milestone.
3. Automated Quality Validation & Defensive Engineering (Part B): 14 automated validation checks (Pandera schema, missing values, audio clipping <0.99, silence ratio <0.40, SNR >=6dB, duration bounds 2-30s, Levenshtein near-duplicate deduplication, intent taxonomy consistency, zero speaker train/test leakage). Empirical results from before.json (failing clipping and silence) vs after.json (100% pass rate). 12/12 adversarial corruption tests caught.
4. Labelling Protocol & Inter-Annotator Agreement (Part C): 120-clip double-annotation cohort across Annotators A1 and A2. Round 1 (Guidelines v1): mean WER = 0.002, Cohen's kappa = 0.8446 with 14 documented intent disagreements across 3 root causes. Round 2 (Guidelines v2): mean WER = 0.000, Cohen's kappa = 0.9889 with 1 residual boundary case resolved by third adjudicator A3. Definition of the 29-clip held-out Gold Test Set (frozen with SHA-256 hash, zero overlap with train/val).
5. Label-Preserving Augmentations & Active Learning Simulation (Part D): 5 distinct acoustic augmentations (MUSAN noise, RIR reverberation, speed 0.9x/1.1x, pitch shift +2 st, MP3/Opus low-bitrate compression) producing 60 clips with quality verification. Real Whisper tiny WER benchmark on clean vs augmented audio. Real active learning simulation evaluating uncertainty sampling vs random baseline across budgets 5-50 over 5 cross-validation folds, showing ~45% label efficiency gain (p < 0.05).
6. Split Generation & Versioning Handoff (Part E): Speaker-disjoint partitions: Train (171 clips, 10 spk), Val (17 clips, 3 spk), Test (29 clips, 4 spk), Cohort B Shifted (32 clips, 2 spk). Total = 249 clips, zero speaker overlap. DVC tracking and frozen SHA-256 handoff document (HANDOFF_A2.md).
7. Appendices: Individual Contribution Table (confirming equal 33.3% contribution across all 3 team members), AI Usage Index, and File Integrity Manifest.

Ensure proper LaTeX math syntax (e.g., \le, \ge, KaTeX / pdflatex compatible), clean table styling with booktabs, and embedded figures for data flow and active learning curves. Keep within the 6-page ceiling before appendices.
"""

---

## Prompt 2: Handoff Document & Checksum Manifest
**Model**: Claude 3.5 Sonnet (Anthropic, build 20241022)  
**Date**: 2026-10-18  
**Output file**: `code/HANDOFF_A2.md`  

**Exact prompt**:
"""
Generate a strict handoff document `code/HANDOFF_A2.md` for Assignment 2 of CS203 Project 5.
Include:
1. Git tag: a1-final
2. SHA-256 checksums of frozen manifests:
   - data/gold_test_set.csv
   - data/splits/train.csv
   - data/splits/val.csv
   - data/splits/test.csv
   - data/splits/cohort_b_shifted.csv
3. Exact clip counts and speaker assignments per split with explicit zero-leakage verification.
4. Rigid constraints: gold_test_set.csv must NEVER be used for model training, prompt tuning, or validation in Assignment 2.
"""

---

## Prompt 3: Project README & Provenance Documentation
**Model**: Claude 3.5 Sonnet (Anthropic, build 20241022)  
**Date**: 2026-10-18  
**Output file**: `README.md`  

**Exact prompt**:
"""
Write a comprehensive, professional root README.md for the STTAI_Project repository.
Include:
1. Executive Project Summary: Voice Helpdesk ASR with Drift-Triggered Retraining.
2. Team Members & Equal Contribution Statement: Explicitly document that all three members (Rajdeep Vraj, Vipul Sunil Patil, Satvik Sharma) contributed equally (33.3% each) across audio collection, pipeline coding, labelling, validation, and reporting.
3. Anonymization Policy: Explain that numeric identifiers (P1-P19 for participants, A1-A3 for annotators) are used in public manifests to strictly preserve personal data privacy while maintaining complete experimental reproducibility and audio provenance.
4. Repository Structure & Artifact Inventory.
5. End-to-end 5-command quickstart to reproduce all validation, agreement, active learning, and split manifests from scratch.
6. Checksum and handoff verification table.
"""
