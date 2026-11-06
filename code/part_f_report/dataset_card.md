# Dataset Card: IITGN-Helpdesk-ASR-v1
<!-- CS203 Assignment 1 - Project 5: Voice Helpdesk ASR -->

## Dataset Description
Code-mixed English–Hindi–Gujarati helpdesk speech collected at IIT Gandhinagar
for the CS203 course project (Assignment 1, 2026-27).
Contains scripted and spontaneous queries across 4 helpdesk categories.

**Purpose**: Train and evaluate a lightweight ASR + intent classification pipeline
for code-mixed multilingual helpdesk queries.

## Source
- Self-collected by team members (Rajdeep Vraj, Vipul Sunil Patil, Satvik Sharma)
  and volunteers from diverse regions.
- Recording sessions conducted during October 2026.
- Speaker consent obtained; all data anonymised (P1 - P19).
- Scripted queries seeded from IIT Gandhinagar FAQs, mess/hostel notices,
  IT-support pages, and course catalogues.

## Size
| Metric | Value |
|--------|-------|
| Total clips | 249 (217 in standard splits + 32 Cohort B) |
| Total duration | 1.25 hours (4516.5 sec) — *Note: below 2.0 h target; compensated via acoustic augmentation* |
| Unique speakers (A1) | 19 (≥15 requirement met) |
| Unique speakers (target) | 30+ (final project) |

## Languages
| Language | Approximate % |
|----------|--------------|
| English (en) | ~25% |
| Hindi (hi) | ~40% |
| Gujarati (gu) | ~35% |
| Code-mixed (en+hi, en+gu, en+hi+gu) | 100% |

## Label Schema
| Label | Type | Values |
|-------|------|--------|
| transcript | Free text | Code-mixed English/Hindi/Gujarati |
| intent | Categorical | admissions, hostel_mess, it_support, student_services |

## Class Balance (Intent)
| Intent | Count | % |
|--------|-------|---|
| admissions | 63 | 25.3% |
| hostel_mess | 62 | 24.9% |
| it_support | 62 | 24.9% |
| student_services | 62 | 24.9% |

## Splits
| Split | Speakers | Clips | Notes |
|-------|----------|-------|-------|
| Train | 13 | 171 | ~79% of partition clips (speaker-disjoint) |
| Val | 2 | 17 | ~8% of partition clips |
| Test (Gold Benchmark) | 4 | 29 | ~13% of partition clips (frozen 100% consensus Gold Set) |
| Cohort B (shifted) | 2 | 32 | Held-out accent/region group (Maharashtra) |

## Metadata Fields
Each clip has: `clip_id`, `speaker_id`, `region`, `device`, `noise_condition`, `lang_mix`,
`sample_rate` (16000), `duration_sec`, `channels` (1), `recording_tool`, `tool_version`,
`collector`, `timestamp_utc`, `sha256_hash`, `script_prompt`.

## Known Limitations
- Background acoustic noise varies by recording environment (dorm room vs quiet office).
- Code-mixing ratio differs across speakers depending on regional background.
- WhatsApp audio lossy compression pre-pipeline is mitigated by standardizing to 16kHz PCM WAV.

## License & Consent
- Anonymised academic research dataset.
- Informed consent obtained from all 19 participants for speech recognition research.
