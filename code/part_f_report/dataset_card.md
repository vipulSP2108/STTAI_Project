# Dataset card — IITGN Voice Helpdesk, final corpus (182 clips)
<!-- CS203 Project 5. Revised 11 Nov 2026; replaces the pilot (249-clip) card, kept in git history. -->

## Description
Code-mixed English–Hindi–Gujarati spoken helpdesk queries recorded by consenting volunteers for
the IIT Gandhinagar voice-helpdesk project. Each clip is labelled with spoken language(s) and one
helpdesk intent by two independent annotators, with expert adjudication of disagreements.

## Size and composition (`final_annotation/consensus_gold_182.json`, `AUDIO_DATA_SUMMARY.json`)
| | |
|---|---|
| Clips | 182 (16 kHz mono WAV), 109.3 min |
| Speakers | 20 (P1–P14, P16, P18–P22); top five give 47 % of clips (Gini 0.36) |
| Intents | admissions 35, hostel_mess 54, it_support 35, student_services 58 |
| Languages (annotator tags) | English 62, Hindi 60, Gujarati 37, code-mixed 23 |
| Labels | intent κ = 0.656 [0.571, 0.741]; 47 clips adjudicated by A3 (test–retest κ 0.652) |
| Transcripts | **none yet** — Round T (`final_annotation/transcription_round/`) pending; the curated strings in `curate_gold_transcripts.py` are withdrawn (`model/results/reference_audit.json`) |
| Splits | speaker-disjoint release split 104 / 38 / 40 (`model/data/splits/release_speakers.json`); Cohort B = P4, P13 |
| Versioning | `model/data/audio.dvc` (dir hash `6ea06a62…`); remote pending |

## Known biases (`model/results/bias_audit.json`)
- **Speaker ↔ intent**: Cramér's V = 0.51; a speaker-only classifier scores 41 % under clip-grouped
  CV. Always split by speaker.
- **Annotator**: A1 and A2 use classes differently (Stuart–Maxwell p < 0.001); A3 sided with A1 in
  31/47 adjudications. Both raw labels are kept.
- **Language ↔ intent**: Gujarati has 1 IT clip of 37; Gujarati clips are short (median 11 s).
- **Duration**: admissions calls median 60 s, student services 18 s — models can learn length.
- **Population**: students only; parents/staff voices absent; four home regions; phones only.
- **Audio**: messaging-app compression before 16 kHz conversion.
- Pilot metadata fields region/device/noise were placeholders; a speaker questionnaire replaces them.

## Intended use
Training and evaluating intent routing and ASR for the course project. Not for speaker
identification, not for any decision about the volunteers.

## Consent and privacy
Volunteers consented to recording and course use; IDs are pseudonymous (P1–P22, A1–A3); no names,
contacts or signed forms are in the repository.
