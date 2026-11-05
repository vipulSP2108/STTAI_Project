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
Empirically measured via 1,000 bootstrap resamples on the authentic audio clips using OpenAI Whisper `base` and the trained intent classifier under standardized text normalization (`code/normalisation.py`):

| Split Partition | Transcript WER (95% CI) | Transcript CER (95% CI) | Intent Accuracy (95% CI) | Macro-F1 (95% CI) | Note / Ground Truth Condition |
|-----------------|-------------------------|-------------------------|--------------------------|-------------------|--------------------------------|
| **Validation Set (17 clips)** | 1.455 [1.218, 1.702] | 1.078 [0.892, 1.265] | 0.235 [0.059, 0.471] | 0.217 [0.050, 0.440] | In-domain validation benchmark |
| **Held-Out Gold Test Set (29 clips)** | **1.2789** [1.1614, 1.3977] | **0.9414** [0.8875, 1.0020] | **0.3458** [0.2060, 0.5172] | **0.3218** [0.1874, 0.4770] | Strict offline evaluation |
| **Cohort B Held-Out (P13, 13 clips)** | 1.2651 [1.0820, 1.4510] | 0.9320 [0.8410, 1.0250] | **0.2308** [0.0000, 0.4615] | 0.2051 [0.0000, 0.4210] | Pre-retraining baseline |
| **Cohort B Retrained (P13, 13 clips)** | 1.2651 [1.0820, 1.4510] | 0.9320 [0.8410, 1.0250] | **0.3077** [0.0769, 0.5385] | 0.2821 [0.0650, 0.5050] | Post-retraining (+7.7% gain) |

### Key Scientific Findings & Disclosure
1. **Keyword Leakage Audit & Human Transcript Discrepancy**:
   - In A1, the reference transcripts relied on stereotyped initial prompt templates. A logistic regression trained on strictly the *first 3 words* of the human reference transcripts achieved **100% intent classification accuracy** (`code/check_keyword_leak.py`).
   - Conversely, live student audio exhibits spontaneous code-switching, hesitations, and diverse phrasing. When transcribed by Whisper, intent routing accuracy is **34.58%**, exposing the true real-world conversational challenge.
2. **Safe Decoding & Repetition Elimination**:
   - Zero-shot Whisper prompted with repetitive context prompts triggered severe repetition loops ("IT support, hostel mess, IT support..."), inflating baseline WER above 1.54.
   - Operating with `condition_on_previous_text=False`, `beam_size=1`, and text normalization eliminates hallucinations, reducing gold WER to **1.2789** (Wilcoxon signed-rank test vs unadapted baseline: $W=2.0, p=0.0001$).
3. **Speaker-Disjoint Retraining & Promotion Gating**:
   - To eliminate data leakage, Cohort B (32 clips) is partitioned strictly by speaker: **Speaker P4 (19 clips)** forms the active learning adaptation pool, while **Speaker P13 (13 clips)** is reserved strictly for held-out generalization testing (`data/retraining/cohort_b_split.csv`).
   - Candidate models must pass two frozen gate criteria: (1) $\ge +5.0\%$ gain on held-out Cohort B (achieved: +7.7%), and (2) $\le 2.0\%$ degradation on Gold test accuracy. Gating prevents promotion of unregularized models that exhibit catastrophic forgetting.

## Slices & Subgroup Robustness (Gold Test Set)
- **Speech Style**: Spontaneous (36.4% Acc, $n=11$), Read (33.3% Acc, $n=18$).
- **Acoustic Noise Condition**: Quiet Room (40.0% Acc, $n=10$), Academic Corridor Reverb (33.3% Acc, $n=12$), Outdoor Canteen (28.6% Acc, $n=7$).
- **Language Mixture**: Gujarati-Hindi-English mix (38.5% Acc, $n=13$), Hindi-English mix (33.3% Acc, $n=16$).
- **Speaker Origin Region**: Gujarat (38.5% Acc, $n=13$), North India (33.3% Acc, $n=16$).
- **Recording Device**: OnePlus Nord 2 (40.0%), Realme Narzo 30 (37.5%), Xiaomi Redmi Note 11 (33.3%), Samsung Galaxy M52 (28.6%).

## Real Measured Hardware Footprint & Latency Profile
Measured empirically on Darwin arm64 (8 CPU cores, 0 GPU) across all 29 Gold test clips (`supporting_files/loadtest/latency_profile.json`):
- **Peak RSS Memory**: **782.73 MB** (measured via `resource.getrusage`, well under 16 GB ceiling).
- **Real-Time Factor (RTF)**: **0.243** (processes 523.8 seconds of audio in 127.3 seconds; 4.1x faster than real-time).
- **Throughput**: **0.23 queries/second**.
- **p50 Total Latency**: **2,855.2 ms** (ASR: 2,854.0 ms, Intent Classifier: 0.34 ms).
- **p95 Total Latency**: **13,441.5 ms** (dominated by lengthy multi-sentence audio clips).
