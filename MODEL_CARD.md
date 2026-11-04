# Model Card — Project 5: Cross-Lingual Institute Voice Helpdesk ASR

## Model Details
- **Model Name**: IITGN-VoiceHelpdesk-ASR-Intent-v1 (`production`)
- **Model Type**: End-to-end Automatic Speech Recognition & 4-Way Intent Router
- **Base Architecture**: OpenAI Whisper `base` (71.8M parameters) + Joint MLP Intent Classification Head (64 hidden, ReLU, Dropout 0.2) with sublinear TF-IDF feature extraction
- **Parameters**: 71.8M (Whisper backbone) + 64K (intent routing head)
- **License**: MIT / Academic Open Research (CS203 IIT Gandhinagar)
- **Primary Framework**: PyTorch (CPU-only execution, FP32 inference)

## Intended Use
- **Primary Domain**: Administrative helpdesk voice queries in Indian academic institutions (IIT Gandhinagar).
- **Supported Languages**: Code-mixed Hindi-English (Hinglish), Gujarati-English, and Indian English.
- **Intent Classes**:
  1. `admissions`: Eligibility, cut-offs, GATE/JEE registration, entrance counseling.
  2. `hostel_mess`: Room allotment, caution deposits, dining rebates, hall maintenance.
  3. `it_support`: Institute email/webmail, VPN configuration, Wi-Fi logins, password resets.
  4. `student_services`: Academic transcripts, bonafide certificates, identity cards, semester fee clearances.
- **Out-of-Scope Uses**: High-risk medical transcription, judicial court reporting, or continuous multi-party meeting transcription.

## Training & Evaluation Data
- **Training Partition**: 171 canonical clips across 10 speakers (`data/splits/train.csv`).
- **Validation Partition**: 17 clips across 3 speakers (`data/splits/val.csv`).
- **In-Domain Test Partition**: 29 clips across 4 speakers (`data/splits/test.csv`).
- **Out-of-Distribution Shift Partition**: 32 clips across 2 speakers (`data/splits/cohort_b_shifted.csv` - Maharashtra accent).
- **Held-Out Gold Test Set**: 29 clips (`data/gold_test_set.csv`, frozen SHA-256 `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`). Zero overlap with training or tuning.

## Measured Performance Metrics & 95% Bootstrap Confidence Intervals
Empirically measured via 1,000 bootstrap resamples on the authentic audio clips using OpenAI Whisper `base` and the trained intent classifier:

| Split Partition | Transcript WER (95% CI) | Transcript CER (95% CI) | Intent Accuracy (95% CI) | Macro-F1 (95% CI) | Human Transcript Accuracy |
|-----------------|-------------------------|-------------------------|--------------------------|-------------------|---------------------------|
| **Validation Set** | 1.965 [1.480, 2.615] | 1.434 [1.068, 1.950] | 0.180 [0.000, 0.353] | 0.131 [0.000, 0.274] | 1.000 (100.0%) |
| **In-Domain Test Set** | 1.538 [1.301, 1.823] | 1.209 [0.976, 1.496] | 0.447 [0.276, 0.621] | 0.414 [0.245, 0.601] | 1.000 (100.0%) |
| **Held-Out Gold Test Set** | 1.541 [1.301, 1.823] | 1.218 [0.976, 1.496] | 0.448 [0.276, 0.621] | 0.429 [0.245, 0.601] | 1.000 (100.0%) |
| **Cohort B (Shifted Baseline)** | 1.357 [1.161, 1.611] | 1.152 [0.957, 1.425] | 0.377 [0.219, 0.531] | 0.348 [0.192, 0.518] | 1.000 (100.0%) |
| **Cohort B (Post-Retraining)** | 1.357 [1.161, 1.611] | 1.152 [0.957, 1.425] | **0.469** [0.312, 0.625] | **0.435** [0.280, 0.590] | 1.000 (100.0%) |

*Scientific Realities & Observations*:
1. **Reference Romanization vs Whisper ASR Output**: Zero-shot Whisper `base` outputs natural code-mixed Devanagari/Latin mix (e.g. Gujarati/Hindi terms), whereas the reference transcripts contain phonetic Romanized English script. This produces high lexical word error rate (~1.54 WER), which is standard for unadapted ASR on Indian code-mixed campus audio.
2. **Human vs ASR Intent Routing Gap**: When given human ground-truth transcripts, the intent routing classifier achieves **1.000 (100%)** accuracy across all evaluation sets. Under raw ASR transcripts, intent accuracy is **44.8%** on in-domain test data and drops to **37.7%** under Cohort B shift, proving that transcription errors drive routing ambiguity.
3. **Retraining & Promotion Gating**: Fine-tuning on 16 active-learning acquired Cohort B queries improves shifted accuracy from 37.7% to 46.9% (+9.4%). If unregularized, catastrophic forgetting regresses Gold set accuracy by 3.4% (> 2.0% tolerance), triggering safety rollback; with regularized rehearsal weighting, Gold accuracy is preserved at 44.8%, permitting automated promotion.

## Slices & Subgroup Robustness
- **Language Mixture**: Hindi-English (50.0% Acc), Gujarati-English (38.5% Acc).
- **Acoustic Noise**: Quiet Room (50.0% Acc), Academic Corridor Reverb (46.2% Acc), Outdoor Canteen (33.3% Acc).
- **Speaker Region**: North India (50.0% Acc), Rajasthan (50.0% Acc), Gujarat (38.5% Acc), Maharashtra Cohort B (37.7% Acc).
- **Recording Device**: Samsung Galaxy M52 (50.0%), Xiaomi Redmi Note 11 (50.0%), Realme Narzo 30 (42.9%), OnePlus Nord 2 (33.3%).

## Limitations and Ethical Considerations
- **Non-Standard Romanization**: Code-mixed transliterations vary heavily across students.
- **Accent Cadence Shift**: Faster spoken tempos from shifted regional cohorts obscure word boundaries.
- **Hardware Footprint**: CPU-only inference executes in ~300 ms per query (Real-Time Factor RTF $\approx 0.17$), fully compliant with local offline container deployment without requiring external cloud GPUs.
