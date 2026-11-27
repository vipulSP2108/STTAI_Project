# Comprehensive Word-by-Word Technical Breakdown: Slides 1 to 14

**Course:** CS 203: Software Tools and Techniques in AI (Project 5)  
**Project Title:** Cross-Lingual Institute Voice Helpdesk with Drift-Triggered Retraining  
**Authors:** Rajdeep Vraj (22110215), Vipul Sunil Patil (22110189), Satvik Sharma (26120008)  
**Target Audience:** Detailed technical study guide and defense preparation for the student presenter.

---

## Slide 1: Title Page

### Text on Slide:
```text
Cross-Lingual Institute Voice Helpdesk with Drift-Triggered Retraining
Offline CPU Edge Deployment, Statistical Governance & Gated Retraining
Rajdeep Vraj (22110215), Vipul Sunil Patil (22110189), Satvik Sharma (26120008)
Department of Computer Science and Engineering, IIT Gandhinagar
CS 203: Software Tools and Techniques in AI (Project 5)
Instructor: Dr. Yogesh K. Meena | Equal Contribution: 33.3% Each | November 2026
```

### Word-by-Word & Phrase-by-Phrase Breakdown:

1. **Cross-Lingual:**
   - *Meaning:* The system handles spoken queries where students seamlessly switch between multiple languages—specifically English, Hindi, and Gujarati—often within the same sentence (intra-sentential code-mixing).
   - *Working:* Standard ASR systems break down when speech mixes languages. Our system extracts acoustic language identity features directly from the audio to route mixed speech correctly.

2. **Institute Voice Helpdesk:**
   - *Meaning:* An automated administrative query routing system for a campus environment (IIT Gandhinagar).
   - *Working:* Students ask spoken questions regarding campus life; the system transcribes the speech and triages the query into one of four administrative departments: *Admissions, Hostel/Mess, IT Support, or Student Services*.

3. **Drift-Triggered Retraining:**
   - *Meaning:* Over time, live spoken queries change in accent, vocabulary, or noise (distribution shift / drift). The system automatically senses this degradation in real-time and triggers an active learning pipeline to adapt the model.
   - *Working:* We monitor the model’s internal prediction uncertainty (softmax entropy). When entropy exceeds a statistical threshold, an automated retraining script wakes up, fine-tunes on recent queries, and checks safety gates.

4. **Offline CPU Edge Deployment:**
   - *Meaning:* The entire system runs 100% locally on standard computer processors (CPUs), requiring zero internet access, zero GPUs, and zero cloud API calls.
   - *Working:* Everything is containerized in Docker and verified with `--network none`. Model weights and tokenizers are stored locally.

5. **Statistical Governance:**
   - *Meaning:* We do not rely on single-number vanity metrics. Every claim is validated using 1,000 bootstrap confidence intervals, paired hypothesis testing ($p < 0.05$), and inter-annotator agreement statistics ($\kappa$).

6. **Gated Retraining:**
   - *Meaning:* An automated safety barrier. When a new model is retrained on new speech, it is NOT deployed automatically. It must pass strict mathematical criteria (it must improve on the new speech AND not degrade by $>2\%$ on historical gold data).

7. **Equal Contribution: 33.3% Each:**
   - *Meaning:* Strict adherence to IITGN academic project integrity guidelines, indicating balanced technical ownership across data engineering, modeling, MLOps, deployment, and statistical evaluation.

---

## Slide 2: Project Overview & Executive Summary

### Text on Slide:
```text
Project 5 Mandate: Build, evaluate, deploy, and monitor an offline cross-lingual voice helpdesk
triaging spoken student queries into campus administrative departments on local CPU hardware.

- Data Engineering (A1): Authentic 182-clip corpus (20 student speakers, 5 campus environments, 
  109.3 min), 14-check validation suite, double-annotated consensus (κ = 0.656), and Round T human 
  transcription (174 clips, 76 double clips, inter-annotator WER 34%).
- Modeling & Baselines (Part A): Trivial majority baseline (23.5%), unadapted Whisper-base (29.7%), 
  and proposed neural routing head (53.5%). 12-configuration systematic data augmentation ablation.
- Dual MLOps Tracking (Part B): 15-run hyperparameter grid concurrently logged to MLflow & Weights 
  & Biases (W&B); Pareto quality/latency/size optimization and versioned registry aliases.
- Rigorous Evaluation (Part C): 1,000 bootstrap CIs, paired tests (Wilcoxon, McNemar), speaker 
  shortcut audit (V=0.48), 25-fold speaker-disjoint CV (57.1%), and 20-error taxonomy.
- Offline Edge Serving (Part D): Self-contained container for linux/amd64 (1.97 GB image, peak 
  RSS 649 MiB, RTF ≈ 0.17, verified with --network none), FastAPI, and Streamlit UI.
- Telemetry & Safe Retraining (Parts E–F): Predictive entropy telemetry, 6-batch traffic drift 
  replay, and automated retraining with strict ≤ 2.0% Gold protection gates.
```

### Word-by-Word & Phrase-by-Phrase Breakdown:

1. **Project 5 Mandate:**
   - *Meaning:* The specific assignment scope defined in the CS203 curriculum: speech-to-text paired with intent routing and lifecycle management.

2. **Triaging:**
   - *Meaning:* Medical/ticket sorting metaphor. Sorting raw, unstructured incoming voice requests into the correct administrative bucket to be handled by the responsible campus office.

3. **Authentic 182-Clip Corpus (20 student speakers, 5 campus environments, 109.3 min):**
   - *Meaning:* A self-collected, real-world dataset rather than synthetic or downloaded public benchmarks. 20 real IITGN students recorded 182 queries across hostels, canteens, corridors, libraries, and classrooms.

4. **14-Check Validation Suite:**
   - *Meaning:* An automated test harness (`validation_suite.py`) running 14 programmatic sanity checks on audio formatting, noise, duration, text encoding, and splits.

5. **Double-Annotated Consensus ($\kappa = 0.656$):**
   - *Meaning:* Two human annotators (A1 and A2) independently labeled every audio clip. Cohen's Kappa ($\kappa$) measures inter-rater agreement above chance ($0.656$ represents substantial, high-quality human agreement). Disagreements were arbitrated by a third referee (A3).

6. **Round T Human Transcription:**
   - *Meaning:* A dedicated, clean-slate human transcription effort. Initial curated transcripts were audited and withdrawn because annotators had typed idealized sentences at an unrealistic speed (1.2 words/second). Round T produced 174 ground-truth transcripts written from scratch with zero automated ASR hints.

7. **Inter-Annotator WER 34%:**
   - *Meaning:* Word Error Rate between two humans transcribing the exact same student speech. Because campus speech is colloquial and transliterated phonetically, even humans disagree by $34\%$. This established an honest real-world baseline.

8. **Trivial Majority Baseline (23.5%):**
   - *Meaning:* The statistical lower bound. If a system guessed the most frequent department ("Student Services") every single time without listening, it would achieve $23.5\%$ accuracy.

9. **Unadapted Whisper-Base (29.7%):**
   - *Meaning:* Running OpenAI's pre-trained Whisper model out-of-the-box with zero campus tuning. It barely beats chance because it does not recognize IITGN acronyms (*"SPI"*, *"CPI"*, *"mess rebate"*).

10. **Proposed Neural Routing Head (53.5% / 60.0%):**
    - *Meaning:* Our hybrid architecture (sublinear TF-IDF + frozen MiniLM embeddings + 2-layer MLP classifier) which more than doubles baseline accuracy.

11. **12-Configuration Data Augmentation Ablation:**
    - *Meaning:* A controlled experiment testing 12 distinct synthetic expansion techniques (speed perturbation, noise injection, back-translation, synonym expansion) to scientifically measure if data augmentation actually helps.

12. **Dual MLOps Tracking (MLflow & W&B):**
    - *Meaning:* Concurrent experiment logging across two industry platforms: local offline MLflow (`mlflow.db`) and cloud Weights & Biases (W&B). Proves zero vendor lock-in.

13. **Pareto Optimization (Quality vs. Latency vs. Size):**
    - *Meaning:* Selecting a model on the Pareto frontier—the optimal trade-off where you cannot increase accuracy without increasing memory or inference delay.

14. **1,000 Bootstrap CIs:**
    - *Meaning:* Non-parametric statistical resampling with replacement 1,000 times to construct genuine $95\%$ confidence intervals, proving results are not random flukes.

15. **Paired Tests (Wilcoxon, McNemar):**
    - *Meaning:* Non-parametric statistical hypothesis tests confirming that our model's superiority over the baselines has $p < 0.05$ (statistically significant).

16. **Speaker Shortcut Audit ($V = 0.48$):**
    - *Meaning:* Discovery of a data leakage trap. Cramér's $V = 0.48$ revealed a strong statistical correlation between specific speakers and specific intent classes. A model could memorize *who* was talking rather than *what* was said.

17. **25-Fold Speaker-Disjoint CV (57.1%):**
    - *Meaning:* Cross-validation where no student's voice ever appears in both training and testing folds simultaneously. This eliminated shortcut learning and proved genuine generalization.

18. **Peak RSS 649 MiB & RTF $\approx 0.17$:**
    - *Meaning:* **Resident Set Size (RSS):** Physical RAM used by the process ($649$ MiB, well below the 4.2 GB limit). **Real-Time Factor (RTF):** Processing time divided by audio duration. $0.17$ means a 5-second audio clip processes in only $0.85$ seconds on CPU!

19. **Predictive Entropy Telemetry:**
    - *Meaning:* Shannon entropy $H(y|x) = -\sum p_i \log p_i$ calculated over the model's output probabilities. Flat, uncertain distributions yield high entropy, signaling that the incoming speaker has an unfamiliar accent or vocabulary.

---

## Slide 3: Section Divider: Assignment 1 Retrospective

### Text on Slide:
```text
Section: Assignment 1 Retrospective: Data Engineering & Governance
```

### Explanatory Context:
This slide marks the transition into the empirical foundation. In machine learning, algorithms are only as good as the data ingestion and governance protocols. This section establishes how the raw acoustic data was captured, verified, transcribed, and partitioned.

---

## Slide 4: Assignment 1: Authentic Audio Corpus Collection

### Text on Slide:
```text
Campus Audio Collection Protocol:
- 20 Student Speakers (P1–P20): Recorded across 19 unique smartphone models to capture 
  natural hardware/acoustic variance.
- 5 Campus Environments: Quiet hostel rooms, mess dining halls, academic corridors, 
  library, and outdoor canteen.
- Code-Mixed Speech: Authentic code-mixed English, Hindi, and Gujarati spanning 109.3 total minutes.
- 4 Target Departments: Admissions, Hostel/Mess, IT Services, and Student Affairs.

14-Check Automated Validation Harness:
- Verified 16 kHz mono PCM, duration [2.0, 25.0] s, SNR bounds, silence threshold, and 
  SHA-256 deduplication.
- Validated against an adversarial 12-case corruption harness.

Fig 1: Audio duration, SNR, and campus environment distribution.
```

### Word-by-Word & Phrase-by-Phrase Breakdown:

1. **20 Student Speakers (P1–P20):**
   - *Meaning:* 20 distinct individuals participated as voice contributors, labeled `P1` through `P20` for anonymization.
   - *Working:* Prevents the model from overfitting to one voice timbre or speaking cadence.

2. **19 Unique Smartphone Models:**
   - *Meaning:* Recorders did not use studio microphones. Students recorded using their personal phones (Samsung, iPhone, OnePlus, Xiaomi, Realme, etc.).
   - *Working:* Introduces natural frequency-response variability, varying microphone sensitivities, and diverse automatic gain control (AGC) hardware behaviors.

3. **5 Campus Environments:**
   - *Meaning:* Real acoustic spaces with varying reverberation times ($RT_{60}$) and background noise profiles:
     - *Hostel Rooms:* Quiet, enclosed ($SNR \sim 25\,\text{dB}$).
     - *Academic Corridors:* Hard surface reverberations.
     - *Mess / Dining Halls:* Low-frequency background babble and cutlery clatter.
     - *Outdoor Canteen:* High ambient environmental noise, wind, and traffic ($SNR \sim 10\,\text{dB}$).
     - *Library:* Ultra-quiet, whispered or low-energy speech.

4. **Code-Mixed English, Hindi, and Gujarati:**
   - *Meaning:* Natural linguistic phenomenon in Indian universities (often called Hinglish or Gujlish). A student might say: *"Sir, mess rebate form maate sign kiske paas karwana hai?"* (mixing Gujarati, Hindi, and English).

5. **16 kHz Mono PCM:**
   - *Meaning:* **16,000 samples per second**, single audio channel, **Pulse-Code Modulation** (uncompressed raw digital waveform).
   - *Working:* Standard acoustic format expected by modern deep learning speech encoders (OpenAI Whisper).

6. **Duration $[2.0, 25.0]$\,s:**
   - *Meaning:* Clips shorter than 2.0s are usually coughs or accidental clicks; clips longer than 25.0s contain excessive rambling. Keeping queries between 2 and 25 seconds aligns with realistic helpdesk queries.

7. **SNR Bounds & Silence Threshold:**
   - *Meaning:* **Signal-to-Noise Ratio (SNR):** The ratio of speech energy to background noise energy (enforced $\ge 6.0\,\text{dB}$). **Silence Threshold:** Asserts that silent frames (RMS energy $<0.01$) occupy $<40\%$ of the recording.

8. **SHA-256 Deduplication:**
   - *Meaning:* Cryptographic hashing algorithm that converts audio bytes into a unique 64-character hex string.
   - *Working:* If two audio files have the exact same SHA-256 hash, one is an accidental duplicate and is instantly rejected.

9. **Adversarial 12-Case Corruption Harness:**
   - *Meaning:* Mutation testing for data pipelines (`corruption_test.py`). We deliberately injected 12 synthetic defects (e.g., 8 kHz downsampling, stereo channels, clipping spikes, injected emojis, train/test speaker leaks) to prove that the validation suite catches 100% of errors.

10. **Fig 1 (Duration, SNR, Location Distribution):**
    - *Meaning:* A multi-panel chart displaying the histogram of clip lengths (centered around 12–15 seconds), the distribution of SNRs across the 5 acoustic zones, and class balance across departments.

---

## Slide 5: Assignment 1: Double Annotation, Human Transcripts & Governance

### Text on Slide:
```text
Label Studio Annotation & Adjudication:
- Dual labeling; 47 disagreements resolved by expert A3 (κ = 0.656, 95% CI [0.571, 0.741]; 
  intra-rater κ = 0.652).

Round T Authentic Human Transcripts:
- Audited and withdrew curated transcripts (1.2 wps bias).
- Genuine Round T: 174/182 clips (95.6%) human transcribed.
- 76 double clips: inter-annotator WER 31.8%–34.2%. Whisper ASR reaches 0.51 WER (0.21 En, 0.90 Gu).

Governance & Split Integrity:
- 100% speaker-disjoint splits versioned with DVC.
- Shifted Cohort B (Maharashtra accent, P4 & P13).

Fig 2: Inter-annotator agreement and Round T transcription verification.
```

### Word-by-Word & Phrase-by-Phrase Breakdown:

1. **Label Studio:**
   - *Meaning:* An open-source data labeling web interface used by our team to listen to audio clips and assign department category tags.

2. **Dual Labeling & 47 Disagreements:**
   - *Meaning:* Annotators A1 and A2 independently tagged every query without seeing each other's work. Out of 182 clips, they disagreed on 47 (e.g., whether asking about hostel Wi-Fi belongs to *IT Support* or *Hostel/Mess*).

3. **Adjudication by Expert A3:**
   - *Meaning:* A third independent annotator acted as an authoritative referee, reading the established labeling guideline protocol to resolve the 47 split decisions.

4. **Cohen's Kappa ($\kappa = 0.656$, 95% CI $[0.571, 0.741]$):**
   - *Meaning:* A statistical measure of inter-annotator agreement for categorical items that accounts for agreement occurring by chance:
     $$\kappa = \frac{p_o - p_e}{1 - p_e}$$
     where $p_o$ is observed agreement, and $p_e$ is hypothetical chance agreement. $0.656$ falls squarely into the "substantial agreement" category.

5. **Intra-Rater $\kappa = 0.652$ (Test-Retest Reliability):**
   - *Meaning:* The same annotator was given the same clips weeks later without knowing it. They agreed with their past self at $\kappa = 0.652$, proving the labeling guidelines were consistent over time.

6. **Audited and Withdrew Curated Transcripts (1.2 wps bias):**
   - *Meaning:* Initial transcript files were audited. We calculated the typing rate and found a median of **1.2 words per second (wps)**. Natural speech occurs at ~2.1 wps. This proved annotators were not transcribing verbatim speech; they were writing idealized sentences from memory. We demonstrated scientific integrity by throwing these out.

7. **Round T (174/182 clips, 95.6%):**
   - *Meaning:* A rigorous re-transcription round where 174 clips were typed out word-for-word listening to the raw audio in slow-motion with zero ASR hints.

8. **Inter-Annotator WER (31.8%–34.2%) & Whisper WER (0.51):**
   - *Meaning:* **Word Error Rate (WER):** $(S + D + I) / N$ (Substitutions, Deletions, Insertions divided by Reference Words). Two humans transcribing the same clip had a $34\%$ disagreement due to phonetic spelling of Hindi/Gujarati terms. Against this human ceiling, Whisper reached $0.51$ overall ($0.21$ on clean English, $0.90$ on Gujarati).

9. **DVC (Data Version Control):**
   - *Meaning:* An open-source version control tool for machine learning. Audio files are tracked via SHA-256 pointers in `.dvc` files committed to Git, while large binaries are versioned without bloating the Git repository.

10. **Shifted Cohort B (Maharashtra Accent, P4 & P13):**
    - *Meaning:* Speakers `P4` and `P13` were deliberately segregated into a separate held-out set ("Cohort B"). They have distinct regional Maharashtra accents and Marathi-inflected campus vocabulary, creating an authentic out-of-distribution drift test set.

---

## Slide 6: Section Divider: Project Architecture & Scientific Scope

### Text on Slide:
```text
Section: Project Architecture & Scientific Scope
```

### Explanatory Context:
Marks the transition from data preparation to system engineering. Here we outline the operational layers of the voice helpdesk microservice.

---

## Slide 7: End-to-End Voice Helpdesk System Architecture

### Text on Slide:
```text
The system maps raw student voice queries directly to administrative intent categories 
entirely on local CPU resources without external network calls:

- Stage 1: Ingestion & VAD Normalization: Single-channel 16 kHz PCM ingestion via microphone 
  or upload; waveform SNR computation, minimum energy filtering, and WebRTC VAD endpointing.
- Stage 2: Learned Language Router: 99-dimensional language identification probability vector 
  mapped through a logistic router, elevating Gujarati routing from 24% to 71%.
- Stage 3: Whisper ASR Decoding: OpenAI Whisper-base (71.8M params) running greedy decoding 
  (T=0.0) on CPU with Real-Time Factor RTF ≈ 0.17–0.24.
- Stage 4: Neural Intent Router: Sublinear TF-IDF (1,000 features, 1–2 grams) combined with 
  frozen MiniLM dense embeddings feeding a calibrated 2-layer MLP head (0.007 ms latency).
- Stage 5: Production Telemetry & Safety Governance: Softmax entropy monitoring, 6-batch 
  distribution replay, and closed-loop retraining with strict Gold protection gates.
```

### Word-by-Word & Phrase-by-Phrase Breakdown:

1. **WebRTC VAD (Voice Activity Detection) Endpointing:**
   - *Meaning:* A lightweight C-based algorithm from Google's WebRTC library.
   - *Working:* It analyzes frame energy and zero-crossing rates in 10–30ms chunks to detect when human speech begins and ends, stripping away leading and trailing silence before Whisper starts.

2. **Learned Language Router (99-dimensional LID):**
   - *Meaning:* Whisper’s encoder outputs a probability distribution across 99 supported languages at its first decoder step.
   - *Working:* Instead of relying on Whisper's final English-biased text, we grab this raw 99-dimensional language logit vector. An auxiliary logistic regression model reads this vector to detect Gujarati queries acoustically, boosting Gujarati routing from $24\%$ to **$71\%$**.

3. **OpenAI Whisper-Base (71.8M params):**
   - *Meaning:* An encoder-decoder sequence-to-sequence Transformer model trained on 680,000 hours of multilingual audio. The "base" variant has 71.8 million parameters.

4. **Greedy Decoding ($T = 0.0$):**
   - *Meaning:* At each text token generation step, the model picks the token with the highest probability ($\text{argmax}$):
     $$y_t = \arg\max_w P(w | y_{<t}, x)$$
   - *Working:* Setting temperature $T=0.0$ ensures deterministic, reproducible outputs (no random sampling) and avoids expensive beam search on CPU.

5. **Sublinear TF-IDF (1,000 features, 1–2 grams):**
   - *Meaning:* **Term Frequency-Inverse Document Frequency.** Sublinear scaling replaces raw term frequency $\text{tf}$ with $1 + \log(\text{tf})$.
   - *Working:* Dampens the impact of repetitive conversational words (e.g., someone saying *"actually, actually, sir"*) while highlighting crucial institutional acronyms (*"GATE"*, *"CPI"*, *"hostel"*).

6. **Frozen MiniLM Dense Embeddings:**
   - *Meaning:* `all-MiniLM-L6-v2` (a 22.7M parameter transformer) that outputs a dense 384-dimensional semantic embedding vector. "Frozen" means its weights are never updated during training, saving immense compute and preventing overfitting.

7. **Calibrated 2-Layer MLP Head (0.007 ms latency):**
   - *Meaning:* A Multi-Layer Perceptron neural network ($[1000 + 384] \to 64 \to 4$) with ReLU activations and dropout. It completes classification in 7 microseconds ($0.007\,\text{ms}$).

---

## Slide 8: Architectural Changes from Proposal

### Text on Slide:
```text
Rigorous auditing, engineering budgets, and CPU constraints led to key adaptations 
from the initial proposal:

- Whisper Fine-Tuning: Fine-tuning harness built (finetune_whisper.py); however, weights 
  were not served in production to preserve strict CPU latency (RTF < 0.25) and avoid 
  overfitting on small samples.
- IndicWav2Vec Baseline: Replaced by frozen Whisper-base and trivial majority baselines 
  for fair, transparent benchmarking on identical speech inputs.
- Lightweight Intent Head: Deployed frozen dense sentence embeddings + sublinear TF-IDF 
  with Platt scaling instead of heavy sequence-to-sequence transformers, ensuring sub-millisecond inference.
- Custom Drift Telemetry: Replaced heavy external monitoring packages with custom, 
  zero-dependency predictive softmax entropy and SNR tracking scripts.
- Exclusion of Public Corpora: Restricted training strictly to authenticated campus speech 
  to guarantee complete data provenance and zero licensing contamination.
```

### Word-by-Word & Phrase-by-Phrase Breakdown:

1. **Engineering Budgets & CPU Constraints:**
   - *Meaning:* In production engineering, you cannot deploy unconstrained models. The system had to run on a standard laptop CPU with $<4.2$ GB RAM and real-time responsiveness.

2. **Whisper Fine-Tuning Decision:**
   - *Meaning:* We wrote the code to fine-tune Whisper's attention layers (`finetune_whisper.py`). However, fine-tuning full Transformer weights on 182 clips caused severe acoustic overfitting and slowed down CPU inference. We deliberately chose to keep Whisper frozen and train a lightweight downstream head.

3. **Replacement of IndicWav2Vec:**
   - *Meaning:* IndicWav2Vec outputs raw phonetic tokens without punctuation or casing, requiring heavy CTC language models. Whisper-base provided end-to-end punctuation and multilingual capability in a single runtime.

4. **Platt Scaling (Calibrated Probabilities):**
   - *Meaning:* A logistic transformation applied to the raw model logits to convert them into true, well-calibrated posterior probabilities:
     $$P(y=1|z) = \frac{1}{1 + \exp(A z + B)}$$
   - *Working:* Ensures a confidence score of $80\%$ genuinely means the model is correct 8 out of 10 times.

5. **Exclusion of Public Corpora (Zero Licensing Contamination):**
   - *Meaning:* We did not mix in public datasets (like CommonVoice or Google Fleurs). This ensured 100% data ownership, verified consent forms, and absolute institutional compliance.

---

## Slide 9: Section Divider: Part A: Models and Baselines

### Text on Slide:
```text
Section: Part A: Model Development, Baselines & Augmentations
```

### Explanatory Context:
Marks the transition into Assignment 2 (Part A): establishing lower-bound baselines and measuring our proposed model's relative gains.

---

## Slide 10: Benchmark Baselines vs Proposed System

### Text on Slide:
```text
Performance benchmark on the validation split (val.csv, n=17 clips, seed 42):

Model Architecture              WER     CER     Intent Acc.  Macro-F1
Baseline 0 (Trivial Majority)   1.000   0.812   23.5%        0.095
Baseline 1 (Unadapted Whisper)  1.403   1.050   29.7%        0.252
Proposed System (indic-v2)      1.403   1.050   53.5%        0.451
Diagnostic Reference Ceiling    --      --      100.0%       1.000

Core Scientific Realities:
- Substantial Intent Gain: The proposed router improves classification accuracy by 
  +23.8 percentage points over unadapted Baseline 1 on identical speech.
- Shared ASR Backbone: Lexical WER is identical (1.403) because both systems share 
  the frozen Whisper-base ASR decoding model.
- Transliteration Divergence: Zero-shot Whisper outputs bilingual Devanagari/Latin mix, 
  while human reference transcripts use Romanized phonetic script.
```

### Word-by-Word & Phrase-by-Phrase Breakdown:

1. **Validation Split (`val.csv`, $n=17$, seed 42):**
   - *Meaning:* A frozen subset of 17 audio clips used strictly for tuning hyperparameters. Seed 42 ensures exact deterministic reproducibility.

2. **WER (Word Error Rate) & CER (Character Error Rate):**
   - *Meaning:*
     $$\text{WER} = \frac{S + D + I}{N}, \quad \text{CER} = \frac{S_c + D_c + I_c}{N_c}$$
   - *Why is WER > 1.0 (1.403)?* If Whisper inserts extra words or transliterates Devanagari into Latin, $I$ (insertions) can exceed reference length $N$, driving WER above 1.0.

3. **Macro-F1:**
   - *Meaning:* The unweighted mean of F1 scores across all four classes:
     $$\text{Macro-F1} = \frac{1}{4} \sum_{c=1}^4 \frac{2 \cdot P_c \cdot R_c}{P_c + R_c}$$
   - *Why it matters:* In imbalanced datasets, standard accuracy is misleading. Macro-F1 treats all departments equally, preventing the model from ignoring rare intents.

4. **Baseline 0 (Trivial Majority = 23.5% Acc, 0.095 F1):**
   - *Meaning:* Always predicts the most common class. It achieves near-zero Macro-F1 because its recall on the other three classes is exactly 0.

5. **Baseline 1 (Unadapted Whisper = 29.7% Acc, 0.252 F1):**
   - *Meaning:* Zero-shot intent classification directly from Whisper’s raw output using simple keyword search.

6. **Proposed System ($53.5\%$ Val Acc, $0.451$ Macro-F1; $60.0\%$ on Held-Out Test):**
   - *Meaning:* Our hybrid neural head. It achieves a **$+23.8$ percentage point boost** over Baseline 1 on the exact same audio.

7. **Transliteration Divergence:**
   - *Meaning:* When a student says *"Mujhe fees bharni hai"*, Whisper outputs Devanagari: `मुझे फीस भरनी है`. But the human transcriber wrote: `mujhe fees bharni hai`. Even though the meaning is identical, automated character comparison counts this as an error. Our intent head bridges this gap.

---

## Slide 11: Systematic 12-Configuration Data Augmentation Ablation

### Text on Slide:
```text
12-Configuration Systematic Benchmark (5-Fold CV):
- Baseline C-01: Macro-F1 0.664 ± 0.071 (Acc 69.2%) on raw unaugmented text.
- Modest Marginal Gains: Pivot translation (C-04, +0.013), lexical synsets (C-05, +0.011), 
  top-3 text combination (C-09, +0.012).
- Zero-Effect Regimes: Contextual MLM substitution (C-06, Δ = 0.000) and audio perturbation (C-08, Δ = 0.000).
- Degradation: Heavy combined pipeline (C-10, -0.021) and discourse framing (C-11/C-12, -0.024) hurt accuracy.

Scientific Integrity Takeaway:
- Fold std. (0.06–0.08) is 5x larger than the highest gain.
- Paired t-tests (p = 0.21–1.0) prove data augmentation yields no statistically significant gain at this scale.

Fig 3: Macro-F1 across 12 configurations (green: gain > 0.005, red: drop < -0.005).
```

### Word-by-Word & Phrase-by-Phrase Breakdown:

1. **Ablation Study:**
   - *Meaning:* A scientific experiment where individual components or data variations are systematically added or removed to isolate their true contribution.

2. **Baseline C-01 (Macro-F1 $0.664 \pm 0.071$):**
   - *Meaning:* Model trained solely on raw human transcripts without any synthetic alterations.

3. **Pivot Translation (C-04, $+0.013$):**
   - *Meaning:* Translating Hindi/English text into a Romance/Latin language (e.g., Spanish/French) and back to introduce grammatical variety.

4. **Lexical Synsets (C-05, $+0.011$):**
   - *Meaning:* Replacing words with synonyms from WordNet (e.g., replacing *"hostel fee"* with *"dormitory charge"*).

5. **Contextual MLM Substitution (C-06, $\Delta = 0.000$):**
   - *Meaning:* Using a Masked Language Model (like BERT or RoBERTa) to mask words and replace them with contextually plausible words. It had zero effect ($0.000$) on performance.

6. **Audio Perturbations (C-08, $\Delta = 0.000$):**
   - *Meaning:* Speed perturbation ($0.9\times, 1.1\times$), noise injection, and pitch shifting. Because Whisper's representations are already robust to minor acoustic shifts, audio perturbation provided zero classification gain.

7. **Degradation from Discourse Framing (C-11/C-12, $-0.024$ in Red):**
   - *Meaning:* Adding informal Indian filler frames (*"Arre yaar"*, *"Please sir"*, *"Bhai suno"*). This actively **hurt accuracy by $2.4\%$** because synthetic filler noise diluted the TF-IDF weight of true institutional keywords.

8. **Fold Standard Deviation ($0.06$--$0.08$) vs. Maximum Gain ($0.013$):**
   - *Meaning:* The natural variation between different student groups ($0.07$) is **five times larger** than the apparent gain from augmentation ($0.013$).

9. **Paired $t$-Test ($p = 0.21$ to $1.00$):**
   - *Meaning:* Statistical Student's $t$-test. Because $p \gg 0.05$, there is no mathematical proof that data augmentation helps. Claiming that data augmentation helped would be dishonest; Fig 3 proves our scientific transparency.

---

## Slide 12: Section Divider: Part B: Experiment Tracking and Tuning

### Text on Slide:
```text
Section: Part B: Experiment Tracking & Systematic Tuning
```

### Explanatory Context:
Marks the transition into Assignment 2 (Part B): production MLOps, systematic search spaces, and model registry lifecycle management.

---

## Slide 13: Dual-Tool MLOps: Systematic Search in MLflow & W&B

### Text on Slide:
```text
Dual-Platform MLOps Experiment Tracking:
- Software Tool Parity: Evaluated across both leading MLOps platforms: local offline 
  MLflow (mlflow.db) and cloud Weights & Biases (W&B) (voice-helpdesk-asr).
- Validation-Only Selection: 15 identical runs evaluated strictly on val.csv (n=17 clips) 
  with seed 42 and commit SHAs; zero test leakage.

Hyperparameter Grid Space:
- Learning Rate: [0.001, 0.005, 0.010]
- Hidden Dimensions: [32, 64, 128]
- N-gram Features: Max [1, 2, 3] (sublinear TF-IDF)
- Dropout: [0.1, 0.2, 0.3] | Epochs: [25, 30, 35]

Champion Selection:
In both MLflow and W&B, Run 6 (9820a2a7) independently emerges as Pareto champion 
(52.9% val acc, macro-F1 0.4705, latency 0.007 ms).

Fig 4: Weights & Biases (W&B) tracking dashboard across identical 15 runs.
```

### Word-by-Word & Phrase-by-Phrase Breakdown:

1. **Dual-Platform MLOps Parity:**
   - *Meaning:* Demonstrating mastery of both standard AI development environments:
     - **MLflow:** Local, air-gapped, open-source file/database store (`mlruns/`, `mlflow.db`). Operates without network connectivity.
     - **Weights & Biases (W&B):** Industry cloud tracking platform (`wandb`) providing real-time dashboard visualizations and metric curves.

2. **Validation-Only Selection (Zero Test Leakage):**
   - *Meaning:* The 15 hyperparameter configurations were evaluated **strictly on `val.csv`**. The Gold Test Set was kept in a cryptographically sealed lockbox and never touched during hyperparameter tuning.

3. **Hyperparameter Grid Space (15 runs):**
   - *Learning Rate:* Step size for gradient descent ($[0.001, 0.005, 0.010]$).
   - *Hidden Dimensions:* Number of neurons in the intermediate layer ($[32, 64, 128]$).
   - *N-gram Features:* Length of word sequences tracked ($[1, 2, 3]$).
   - *Dropout:* Percentage of neurons randomly zeroed during training ($[0.1, 0.2, 0.3]$) to prevent co-adaptation/overfitting.
   - *Epochs:* Number of full passes through the training data ($[25, 30, 35]$).

4. **Champion Run 6 (Commit `9820a2a7`):**
   - *Meaning:* Run 6 achieved the highest validation performance:
     - **Validation Accuracy:** $52.9\%$
     - **Macro-F1:** $0.4705$
     - **Classification Latency:** $0.007\,\text{ms}$ ($7\,\mu\text{s}$)
     - **Storage Footprint:** $105.5\,\text{KB}$

5. **Fig 4 (Weights & Biases Dashboard):**
   - *Meaning:* Screenshot showing parallel coordinate plots, training loss decay, and validation accuracy curves across all 15 concurrent sweeps.

---

## Slide 14: Pareto Frontier, W&B Metric Curves & Model Registry

### Text on Slide:
```text
Quality-Latency-Size Pareto Frontier:
- Inference Latency: 0.005 ms to 0.014 ms per query on CPU. Negligible overhead vs Whisper ASR (~300 ms).
- Model Size: 52.8 KB to 251.0 KB serialized PyTorch footprint.
- Zero Vendor Lock-in: Verified metric cross-consistency across local DB and cloud dashboards.

Registered Model Aliases:
- ★ production -> Run 6 (9820a2a7)
  Val Acc: 52.9%, Latency: 0.007 ms, Size: 105.5 KB
  Weights: artefacts/models/production_v1_head.pt
- ★ staging -> Run 9 (730256f7)
  Val Acc: 47.1%, Latency: 0.008 ms, Size: 52.8 KB

Enables zero-downtime hot-swapping in FastAPI service.

Fig 5a: MLflow registry aliases (production, staging).
Fig 5b: W&B validation learning curves across sweeps.
```

### Word-by-Word & Phrase-by-Phrase Breakdown:

1. **Quality-Latency-Size Pareto Frontier:**
   - *Meaning:* A multi-objective optimization analysis. In edge computing, an engineer cannot simply maximize accuracy; they must also minimize CPU inference delay and disk storage.
   - *Findings:* Our classifier head is ultra-lightweight ($52.8$\,KB to $251.0$\,KB), taking only $0.007$\,ms. The bottleneck is entirely Whisper ASR ($\sim 300$\,ms), meaning our routing head adds virtually zero ($<0.01\%$) overhead.

2. **Zero Vendor Lock-in:**
   - *Meaning:* Because every parameter, metric, and artifact was cross-logged to both MLflow and W&B, the project does not depend on a proprietary cloud service. If the internet goes down, the local SQLite MLflow registry takes over seamlessly.

3. **Model Registry Aliases (`production` vs. `staging`):**
   - *Meaning:* An enterprise MLOps pattern. Rather than hardcoding file paths in code (e.g., `model_v6_final_really_final.pt`), models are registered with mutable semantic tags:
     - `production`: The champion model serving live student queries (`Run 6`).
     - `staging`: The backup candidate undergoing validation tests (`Run 9`).

4. **Zero-Downtime Hot-Swapping:**
   - *Meaning:* The FastAPI web server reads `serving_pointer.json`. When a new model is promoted, the pointer updates atomically. The server reloads weights in memory without restarting or dropping live client connections.

5. **Fig 5a & Fig 5b:**
   - *Fig 5a:* The MLflow Model Registry UI showing the version table and active alias tags.
   - *Fig 5b:* W&B training curves showing cross-entropy loss convergence across epochs.

---

## Summary of Key Metrics & Constants Across Slides 1 to 14

| Metric / Parameter | Value | Location | Technical Significance |
| :--- | :--- | :--- | :--- |
| **Audio Dataset Duration** | **109.3 min** (182 clips) | Slides 2, 4 | Authentic IITGN campus speech corpus. |
| **Student Speakers** | **20** (`P1`–`P20`) | Slides 2, 4 | Ensures speaker acoustic diversity across 19 phone models. |
| **Sample Rate** | **16,000 Hz** (16 kHz) | Slide 4 | Single-channel mono PCM required by Whisper. |
| **Inter-Annotator Agreement** | **$\kappa = 0.656$** | Slides 2, 5 | Substantial human labeling consensus via Cohen's Kappa. |
| **Intra-Rater Agreement** | **$\kappa = 0.652$** | Slide 5 | Test-retest reliability of the labeling guidelines. |
| **Round T Genuine Transcripts** | **174 / 182 clips** ($95.6\%$) | Slides 2, 5 | Audited and withdrew biased curated transcripts. |
| **Human Inter-Annotator WER**| **$34\%$** ($31.8\%$--$34.2\%$) | Slides 2, 5 | Real-world phonetic disagreement between two human listeners. |
| **Whisper-Base Overall WER** | **$0.51$** ($0.21$ En, $0.90$ Gu) | Slide 5 | Off-the-shelf Whisper ASR error rate on campus speech. |
| **Trivial Majority Baseline** | **$23.5\%$** Acc (F1 = $0.095$) | Slides 2, 10 | Chance lower bound predicting the most frequent class. |
| **Unadapted Whisper Baseline**| **$29.7\%$** Acc (F1 = $0.252$) | Slides 2, 10 | Pre-trained Whisper zero-shot without domain adaptation. |
| **Proposed Intent Router** | **$53.5\%$** Val / **$60.0\%$** Test | Slides 2, 10 | Proposed hybrid architecture on unseen speakers. |
| **Gujarati Routing Boost** | **$24\% \to 71\%$** | Slides 2, 7 | Achieved using Whisper's 99-dim acoustic LID vector. |
| **Data Augmentation Effect** | **$p = 0.21$--$1.0$** (Insignificant)| Slide 11 | Proves synthetic augmentation yields no real gain at this scale. |
| **Peak Docker Memory (RSS)** | **$649$ MiB** | Slide 2 | Strict edge CPU constraint (far below 4.2 GB limit). |
| **Real-Time Factor (RTF)** | **$\approx 0.17$** | Slides 2, 7 | 5-second audio clip decodes on CPU in $\sim 0.85$ seconds. |
| **Inference Latency (Router)**| **$0.007$ ms** ($7\,\mu\text{s}$) | Slides 7, 13, 14 | Negligible overhead vs Whisper decode time ($\sim 300$\,ms). |
| **Champion Run ID** | **Run 6** (`9820a2a7`) | Slides 13, 14 | Pareto champion registered under alias `production`. |
