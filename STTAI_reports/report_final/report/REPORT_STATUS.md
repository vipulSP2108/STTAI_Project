# REPORT_STATUS.md — what is verified, what is not (revised 11 Nov 2026)

The previous version of this file claimed several things that were not true. They are corrected here.
See `docs/INSTRUCTOR_GRADE_2026-11-11.md` for the full grading and `docs/MANUAL_TASKS.md` for what
the team still has to do by hand.

## Corrections to earlier claims
| Earlier claim | Status |
|---|---|
| Curated transcripts verified against audio "across 100+ clips" | **False.** No such pass exists. `model/results/reference_audit.json` shows the curated strings do not match the audio (median 1.2 words/s; independent ASR systems disagree with them). They are withdrawn as references. |
| `--network none` verified with 783 MB RAM, 3.84 GB image | **False.** 783 MB was a macOS host measurement; 3.84 GB was never measured. The only container evidence is Satvik's Windows build: image 1,971,418,582 bytes, `supporting_files/revised_validation.json` (p50 5.0 s, p95 38.1 s, peak RSS 649 MiB, 40 clips). |
| Unseen-speaker accuracy 75.0 % | **Withdrawn.** Fold-1 speakers all appear in training. Speaker-disjoint result: 55.2 % ± 10.4 (`model/results/speaker_cv_intent_asr_hybrid.json`). |
| End-to-end 71.4 % vs reference-text 87.4 % | **Withdrawn.** Clip-grouped folds and curated references. |
| Expert intra-rater κ = 0.625 | Typo. `expert_reliability_report.json` gives 0.652 (6/8 repeats), which the report uses. |
| Pilot κ 0.723 → 0.845 | **Withdrawn.** Computed from script-generated exports. |

## Verified numbers that can stay
- 182 clips, 20 speakers, 109.3 min; intent κ = 0.656 [0.571, 0.741]; 47 adjudicated; test–retest 6/8.
- Text-augmentation funnel 1,557 → 701.
- Speaker-disjoint intent results, bias audit, reference audit, audio robustness (this session).
- Docker revised image build and offline validation on Windows (Satvik, `82e2ce2`).

## Not yet done
- Human transcripts (Round T) → inter-annotator WER, true WER, Whisper fine-tuning.
- Docker tarball + SHA-256, second-machine load, hosted CI run.
- Report PDFs must be rebuilt from the revised `.tex` files.
