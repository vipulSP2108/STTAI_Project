# Model card — Voice Helpdesk router `indic-v2-lid-router-b3-expert`

Revised 11 Nov 2026. Replaces the earlier card, whose WER figures used withdrawn reference text.

## Intended use
Route short spoken queries to one of four IIT Gandhinagar helpdesk queues (admissions,
hostel/mess, IT support, student services) and show a transcript. Assistive only: a person
handles the query, and low-confidence or unrouted queries should go to a general desk.
Not for decisions about individuals, not for languages other than English/Hindi/Gujarati.

## System
| Stage | Component | Version |
|---|---|---|
| Language routing | Logistic regression on Whisper-base 99-language log-probabilities → en/hi/gu | trained in image on train+val speakers |
| ASR (hi) | `vasista22/whisper-hindi-small`, CTranslate2 int8 | `fb4a24afc20c42906deed31c3689e4be31da41fe` |
| ASR (gu) | `vasista22/whisper-gujarati-base`, CTranslate2 int8 | `59c972a6f00f529efc7c9b631dff338157561ed9` |
| ASR (en) + LID | `Systran/faster-whisper-base` int8 | `ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66` |
| Intent | char 2–5-gram TF-IDF + MiniLM whole-query and opening-topic embeddings, trained on expert-final labels, LR (C=0.3 chosen on validation) | MiniLM `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` |

Decoding: greedy, VAD, no prompt (the old domain prompt caused copy loops). CPU only.

## Data
182 clips, 20 speakers, 109 min, intents double-annotated (κ = 0.656) with expert adjudication.
Release split by speaker: 104 train / 38 validation / 40 test. Router training text is ASR output,
not human transcripts (none exist yet). See `STTAI_reports/report_final/report/report_A1.tex`.

## Metrics (all speaker-disjoint)
| Evaluation | Result | File |
|---|---|---|
| 5-fold × 5-seed speaker CV, intent accuracy (B3, expert labels) | 53.6 % ± 9.1, macro-F1 0.502 (majority 24.4 %; soft-label B7 57.1 %) | `model/results/intent_v2_ablation_asr_hybrid*.json` |
| Release test, 40 clips, 4 unseen speakers (text-level) | 60.0 % [52.5, 78.9], macro-F1 0.609; previous router 47.5 %; McNemar p = 0.125 (soft-label variant, first run: 57.5 %) | `model/results/release_eval.json` |
| Language routing, speaker CV | 81.1 % (Gujarati 71 %) vs 74.4 % for restricted argmax | `model/results/lid_router.json` |
| End-to-end in container, `--network none`, 40 test clips | intent 60.0 %, macro-F1 0.602, routing 75 %, peak RAM 2.0 GB (latency on emulated amd64/M1: p50 40 s, RTF 2.0) | `supporting_files/docker_indic_v2/indic_v2_validation.json` |
| Transcript WER | **not reported** until human transcripts exist | — |

## Slices and weak groups
Accuracy by language (B3, CV): English 68 %, Hindi 58 %, code-mixed 48 %, Gujarati 41 %; on the release test: English 89 %, Hindi 65 %, Gujarati 29 %, code-mixed 25 %.
Clips under 15 s are weakest (≈48 %). Per-speaker leave-one-out accuracy ranges 0–100 %; the
largest contributor (P13, 22 clips) is at 32 %. Lowest recall (CV): admissions 43 %, student services 47 %.

## Limitations and risks
- Labels: 74 % raw inter-annotator agreement; annotators differ in class usage (Stuart–Maxwell p < 0.001).
- Tiny test set (40 clips, 4 speakers): wide intervals; v2 vs v1 not significant.
- Gujarati is under-served at every stage (routing, ASR, intent) — a fairness risk for Gujarati speakers.
- Confidence separates right from wrong only weakly (0.46 vs 0.36); do not use it to auto-close tickets.
- Speakers are students; parents and staff are under-represented; accents outside the four regions are untested.
- Audio of consenting volunteers only; no audio is stored by the service, requests are logged without content.
