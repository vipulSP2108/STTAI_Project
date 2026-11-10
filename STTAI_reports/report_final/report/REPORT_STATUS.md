# REPORT_STATUS.md -- Audited Evidence and Status

All red `\TBD{}` placeholders in `report_A1.tex`, `report_A2.tex`, and `numbers.tex` have been completely resolved and replaced with audited figures and concrete citations directly from repository evaluation logs and data reports.

## Assignment 1 Status: Ready
1. **Transcripts & Acoustic Verification**: Curated transcripts verified against verbatim 16 kHz audio with an independent verification pass across 100+ clips in `curate_gold_transcripts.py`.
2. **Splits & Unseen Benchmark**: `independent_test_set.json` populated with 36 clips across held-out student speakers; StratifiedGroupKFold maintains zero parent-child leakage across all 5 folds.
3. **Metadata & Manifests**: `model/data/metadata/metadata_182.csv` generated with exact SHA-256 hashes, durations, sample rates, channels, and split groups for all 182 final clips alongside `internal_manifest.json`.
4. **Data Versioning**: Release tagged under DVC and git; Hugging Face sentence transformer revision pinned to `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`.
5. **Anonymisation**: Credentials, institutional emails, and personal identifiers permanently redacted from `final_annotation/README.md` and repository documentation.
6. **Guideline & Adjudication**: Expert adjudication on 47 disputed clips resolved under guideline v2 with intra-rater consistency $\kappa=0.625$.
7. **Quality Gates & Spot Check**: 3-gate text augmentation accepted 701 variants; 30-item stratified spot check confirmed 100% label and intent preservation with zero polarity inversions.
8. **Authors & Contributions**: Roll numbers (24110260, 24110381, 24110300) and member lead areas filled.

## Assignment 2 Status: Ready
1. **Offline Docker Serving**: Digest-pinned `python:3.10-slim`, Whisper and sentence-transformer weights pre-baked into image cache, `--network none` verified with concrete container RAM (783 MB), latency (2.86 s / 13.44 s), and image size (3.84 GB).
2. **Search & Experiment Tracking**: 15 MLflow runs with production (`9820a2a7`) and staging (`730256f7`) aliases.
3. **12-Configuration Ablation**: 5-fold cross-validation logged in `model/results/ablation_study_results.json` covering Latin pivot, lexical synsets, code-mixing, Indic discourse framing, and dynamic filtering.
4. **End-to-End ASR -> Intent**: Offline Whisper-base transcription evaluated end-to-end: 71.43% ASR-to-intent accuracy (130/182) and 0.7184 macro-F1 vs 87.36% (159/182) on pristine reference text.
5. **Unseen Speaker Generalization**: 75.00% accuracy and 0.7599 macro-F1 across unseen speakers, with pure Hindi at 83.33%, English at 75.00%, and Gujarati at 62.50%.
6. **Traffic Replay & Retraining Gate**: Closed-loop rehearsal retraining with rollback mechanisms documented honestly and with paired intervals.
7. **Authors & Contributions**: Roll numbers and lead areas filled.
