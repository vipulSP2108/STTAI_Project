# Presentation Speaking Script & Slide Outline Guide

**Course:** CS 203: Software Tools and Techniques in AI (Project 5)  
**Project Title:** Cross-Lingual Institute Voice Helpdesk with Drift-Triggered Retraining  
**Team Members:** Rajdeep Vraj (22110215), Vipul Sunil Patil (22110189), Satvik Sharma (26120008)  
**Estimated Presentation Duration:** 10–12 minutes (~30–45 seconds per slide)  
**Slide Deck:** `presentation/slides.pdf` (compiled from `presentation/slides.tex` / `PPT_in_IEEE_format/main.tex`)

---

## Strategic Presenter Guidelines

1. **Academic Demeanor & Scientific Rigor:** Speak with confidence and technical precision. Ground every claim in empirical data (sample sizes, $p$-values, $95\%$ bootstrap confidence intervals, and Real-Time Factor).
2. **Emphasize Course Tools Early & Often:** Highlight **MLflow, Weights & Biases (W&B), DVC, Docker, Label Studio, and FastAPI**. Point out that we achieved true MLOps parity across both local and cloud platforms.
3. **Showcase Intellectual Honesty:** Professors deeply appreciate uncovering vulnerabilities rather than hiding them. Emphasize our discovery of **speaker shortcut bias ($V=0.48$)**, the audit and withdrawal of flawed curated transcripts, and the empirical demonstration of **catastrophic forgetting ($62.5\% \to 30.0\%$)** that our safety gate caught.
4. **Time Management:** Keep transitions crisp. Do not read the slides verbatim; speak to the insights *behind* the bullet points while letting the visual figures tell the story.

---

## Slide-by-Slide Outline, Speaking Script & Defense Prep

---

### Slide 1: Title Page
- **Slide Title:** Cross-Lingual Institute Voice Helpdesk with Drift-Triggered Retraining
- **Subtitle:** Offline CPU Edge Deployment, Statistical Governance & Gated Retraining
- **Visual Focal Point:** Clean IEEE CambridgeUS Dolphin plum layout, author roll numbers (22110215, 22110189, 26120008), IIT Gandhinagar affiliation.

#### Verbatim Presenter Script:
> "Good morning, Professor Meena and colleagues. Today, our team—Rajdeep Vraj, Vipul Sunil Patil, and Satvik Sharma—is proud to present our final course project: an End-to-End Cross-Lingual Institute Voice Helpdesk with Drift-Triggered Retraining.
>
> Our mandate was to build a complete, production-grade MLOps pipeline capable of triaging spoken multilingual student administrative queries entirely on local CPU edge hardware—with zero cloud leakage, rigorous statistical verification, online telemetry, and automated, safety-gated retraining."

#### Anticipated Professor Question & Defense:
- **Q:** *Why emphasize offline CPU deployment instead of using a cloud LLM or cloud speech API?*
- **A:** *Campus administrative queries involve sensitive student data—transcripts, financial aid, and disciplinary inquiries—which must comply with institutional privacy protocols. Furthermore, edge CPU deployment guarantees zero per-query API cost, deterministic sub-second latency ($RTF \approx 0.17$), and operational resilience without depending on external network connectivity.*

---

### Slide 2: Project Overview & Executive Summary
- **Slide Title:** Project Overview & Executive Summary
- **Visual Focal Point:** Structured roadmap covering A1 data engineering, Part A baselines, Part B dual MLOps, Part C evaluation, Part D Docker, and Part E telemetry/retraining.

#### Verbatim Presenter Script:
> "To give you an executive overview of our technical journey:
> We began in Assignment 1 by collecting an authentic 182-clip campus audio corpus across 20 student speakers, enforcing a 14-check validation suite, double-annotated consensus, and an authentic human transcription round known as Round T.
>
> In Assignment 2, we moved from simple heuristic baselines to a neural routing head, tracked 15 systematic hyperparameter runs across both MLflow and Weights & Biases, conducted 1,000 bootstrap confidence interval evaluations, and packaged the system into a self-contained 1.97 GB Docker container running on CPU with peak RSS of 649 MiB.
>
> Finally, we built an online entropy monitoring system that detects real-time accent drift and enforces a rigid two-stage promotion gate preventing catastrophic forgetting."

---

### Slide 3: Section Divider: Assignment 1 Retrospective
- **Slide Title:** Assignment 1 Retrospective: Data Engineering & Governance
- **Visual Focal Point:** Section header box.

#### Verbatim Presenter Script:
> "Let us briefly revisit our Assignment 1 data foundation, which established the empirical bedrock for everything we built in Assignment 2."

---

### Slide 4: Assignment 1: Authentic Audio Corpus Collection
- **Slide Title:** Assignment 1: Authentic Audio Corpus Collection
- **Visual Focal Point:** Left: 20 speakers, 19 phone models, 5 campus locations, 14-check suite. Right: Fig 1 (duration, SNR, and location distribution).

#### Verbatim Presenter Script:
> "Our dataset consists of 182 authentic spoken audio queries totaling 109.3 minutes, recorded across 20 student speakers using 19 distinct smartphone models.
>
> We captured natural acoustic diversity by recording in five realistic campus environments: Academic Blocks, Student Hostels, Outdoor Canteens, Sports Complexes, and the Library.
>
> Every clip passed through our automated 14-check sanity validation suite—verifying 16 kHz sampling, SNR thresholds, clipping boundaries, and metadata integrity with zero manual overrides."

---

### Slide 5: Assignment 1: Double Annotation, Human Transcripts & Governance
- **Slide Title:** Assignment 1: Double Annotation, Human Transcripts & Governance
- **Visual Focal Point:** Left: Label Studio double annotation ($\kappa = 0.656$), Round T genuine human transcripts ($174/182$ clips, $34\%$ WER), DVC versioning. Right: Fig 2 (Inter-annotator agreement).

#### Verbatim Presenter Script:
> "To ensure rigorous data governance, annotators A1 and A2 independently labeled the dataset in Label Studio. All 47 disagreements were adjudicated by an expert referee, yielding a strong inter-annotator Cohen's kappa of 0.656 and an intra-rater test-retest reliability of 0.652.
>
> Crucially, when we audited our initial curated reference transcripts, we discovered an unrealistic typing speed of 1.2 words per second, indicating annotators had written idealized scripts rather than verbatim speech. We immediately withdrew them and conducted Round T: transcribing 174 clips from scratch with zero ASR pre-fills.
>
> 76 double-annotated clips established an authentic human inter-annotator WER of 31.8% to 34.2%, against which Whisper achieved a realistic 0.51 WER. All splits were versioned via DVC with 100% speaker-disjoint isolation."

#### Anticipated Professor Question & Defense:
- **Q:** *Why is human inter-annotator WER around 34%? Isn't that high?*
- **A:** *In real-world spontaneous campus speech, students mix English, Hindi, and Gujarati colloquialisms with informal phonetic variations and background canteen noise. Two different humans spelling transliterated Gujarati words phonetically produce natural character differences. Acknowledging this 34% human variance is essential for establishing an honest acoustic baseline.*

---

### Slide 6: Section Divider: Project Architecture & Scientific Scope
- **Slide Title:** Project Architecture & Scientific Scope
- **Visual Focal Point:** Section header box.

#### Verbatim Presenter Script:
> "Next, let us examine the end-to-end system architecture and the deliberate engineering pivots we made from our initial proposal."

---

### Slide 7: End-to-End Voice Helpdesk System Architecture
- **Slide Title:** End-to-End Voice Helpdesk System Architecture
- **Visual Focal Point:** Four-stage pipeline: Audio Ingestion $\to$ Whisper Greedy ASR $\to$ Hybrid Representation $\to$ Lightweight Intent Head.

#### Verbatim Presenter Script:
> "Our inference pipeline takes raw student voice queries directly to administrative intent categories entirely on local CPU resources:
> First, audio is resampled to 16 kHz mono and gated via WebRTC Voice Activity Detection.
>
> Second, OpenAI Whisper-base performs deterministic greedy decoding at temperature zero, delivering real-time transcription in approximately 300 milliseconds.
>
> Third, we extract a hybrid feature representation: sublinear word and character TF-IDF capturing campus-specific vocabulary, concatenated with 384-dimensional dense semantic embeddings from frozen MiniLM.
>
> Finally, a compact 2-layer MLP classifier triages the query into one of four administrative departments: Academic, Hostel, Accounts, or Admin."

---

### Slide 8: Architectural Changes from Proposal
- **Slide Title:** Architectural Changes from Proposal
- **Visual Focal Point:** Three clear engineering evolution points: Decoupled ASR + Intent Head, 40-word opening window, and learned 99-dim LID router.

#### Verbatim Presenter Script:
> "Rather than sticking blindly to our initial proposal, we made three evidence-based engineering adaptations:
> First, we abandoned a heavy end-to-end speech classifier in favor of a decoupled ASR plus lightweight neural head. This cut inference RAM to just 649 MiB, well beneath the 4.2 GB platform limit.
>
> Second, our error analysis showed 35% of test mistakes were caused by conversational preamble. We introduced a 40-word opening window normalizer that isolates the core request and boosts cross-validation accuracy.
>
> Third, code-mixed Gujarati queries initially collapsed into Hindi script. We extracted Whisper's 99-dimensional acoustic language identification logits, tripling Gujarati routing accuracy from 24% to 71%."

---

### Slide 9: Section Divider: Part A: Baseline Development & Augmentation Experiments
- **Slide Title:** Part A: Baseline Development & Augmentation Experiments
- **Visual Focal Point:** Section header box.

#### Verbatim Presenter Script:
> "In Part A, we benchmarked our proposed architecture against standard baselines and conducted a systematic data augmentation ablation."

---

### Slide 10: Benchmark Baselines vs Proposed System
- **Slide Title:** Benchmark Baselines vs Proposed System
- **Visual Focal Point:** Comparative table with Majority, Whisper Zero-Shot, and Proposed System across Train, Val, Release Test, and Latency.

#### Verbatim Presenter Script:
> "As shown in this comparison table:
> The trivial majority class baseline achieves 23.5% validation accuracy, representing pure chance.
>
> Zero-shot unadapted Whisper-base achieves 29.7% on validation and 32.5% on test, struggling because generic pre-trained models do not understand campus acronyms like SPI, CPI, or mess rebates.
>
> Our proposed neural routing head achieves 52.9% on validation and 60.0% on the unseen release test set—more than doubling the accuracy of the zero-shot baseline while requiring just 0.007 milliseconds for classification."

---

### Slide 11: Systematic 12-Configuration Data Augmentation Ablation
- **Slide Title:** Systematic 12-Configuration Data Augmentation Ablation
- **Visual Focal Point:** Left: 12 augmentation variants (speed, noise, gain, pitch, mask). Right: Fig 3 (Augmentation ablation delta chart).

#### Verbatim Presenter Script:
> "To improve acoustic robustness, we evaluated 12 systematic data augmentation configurations:
> Speed perturbations between 0.9x and 1.1x, synthetic campus noise injection across SNR levels, gain variations, pitch shifting, and time-frequency masking.
>
> The data revealed a critical insight: mild speed perturbation at 0.95x and 1.05x yielded a statistically solid +2.3% validation gain. However, aggressive noise injection below 10 dB SNR degraded Whisper's greedy decoding, introducing phonetic hallucinations.
>
> Consequently, we retained only conservative speed perturbation for final model training."

---

### Slide 12: Section Divider: Part B: Experiment Tracking & Systematic Tuning
- **Slide Title:** Part B: Experiment Tracking & Systematic Tuning
- **Visual Focal Point:** Section header box.

#### Verbatim Presenter Script:
> "Part B focuses on MLOps best practices: systematic hyperparameter optimization concurrently tracked in both MLflow and Weights & Biases."

---

### Slide 13: Dual-Tool MLOps: Systematic Search in MLflow & W&B
- **Slide Title:** Dual-Tool MLOps: Systematic Search in MLflow & W&B
- **Visual Focal Point:** Left: 15-run grid search across LR, hidden dims, n-grams, dropout. Right: Fig 4 (Weights & Biases runs dashboard).

#### Verbatim Presenter Script:
> "A core strength of our project is dual-platform MLOps parity. We conducted a 15-run systematic hyperparameter grid search, logging all runs concurrently to local offline MLflow and cloud Weights & Biases.
>
> All 15 runs were evaluated strictly on the validation set with fixed seed 42 and git commit SHAs, guaranteeing zero test leakage.
>
> Both MLflow and W&B independently converged on Run 6—commit 9820a2a7—as the champion configuration, achieving 52.9% validation accuracy and a macro-F1 of 0.4705 with an inference latency of just 7 microseconds."

---

### Slide 14: Pareto Frontier, W&B Metric Curves & Model Registry
- **Slide Title:** Pareto Frontier, W&B Metric Curves & Model Registry
- **Visual Focal Point:** Left: Pareto frontier metrics, Registered Aliases (`production` vs `staging`). Right: Fig 5a (MLflow aliases) and Fig 5b (W&B validation curves).

#### Verbatim Presenter Script:
> "Here we analyze the Pareto frontier across quality, latency, and model size.
> Across all 15 models, classification latency ranged from 5 to 14 microseconds, and serialized PyTorch weights remained under 250 kilobytes.
>
> In our Model Registry, we assigned explicit versioned aliases: Run 6 was promoted to `production`, while Run 9 was designated as `staging`.
>
> This formal registry structure allows our FastAPI service to load models by alias rather than hardcoded file paths, enabling zero-downtime hot-swapping in production."

---

### Slide 15: Section Divider: Part C: Unified Evaluation, Statistics & Errors
- **Slide Title:** Part C: Unified Evaluation, Statistics & Errors
- **Visual Focal Point:** Section header box.

#### Verbatim Presenter Script:
> "In Part C, we subjected our system to rigorous statistical verification, including bootstrap confidence intervals, hypothesis testing, and a 20-failure mode audit."

---

### Slide 16: Unified Evaluation Across Splits & 1,000 Bootstrap CIs
- **Slide Title:** Unified Evaluation Across Splits & 1,000 Bootstrap CIs
- **Visual Focal Point:** Metrics table showing Train, Val, Gold Test, and Cohort B with exact 95% bootstrap confidence intervals.

#### Verbatim Presenter Script:
> "Rather than reporting single-point accuracy estimates, we built an evaluation engine executing 1,000 non-parametric bootstrap resamples to compute empirical 95% confidence intervals.
>
> On the held-out Gold Test Set of 40 unseen student queries, our production model achieved 60.0% accuracy with a 95% confidence interval of 45.0% to 75.0%, and a macro-F1 of 0.589.
>
> On the out-of-domain Cohort B drift set, performance dropped to 42.9%, empirically confirming the presence of distribution shift."

---

### Slide 17: Paired Significance Tests & Keyword Leakage Audit
- **Slide Title:** Paired Significance Tests & Keyword Leakage Audit
- **Visual Focal Point:** Left: Wilcoxon and McNemar test statistics ($p < 0.05$), Keyword template leakage audit. Right: Fig 6 (Gold WER substitution/deletion/insertion breakdown).

#### Verbatim Presenter Script:
> "To confirm that our improvements were genuine, we executed paired statistical tests. Both the Wilcoxon signed-rank test and McNemar's test yielded p-values below 0.05, confirming that our neural routing head significantly outperforms both the Majority baseline and Zero-Shot Whisper.
>
> Furthermore, we performed an academic integrity audit for keyword template leakage. We discovered that three specific administrative words occurred across both training and test templates. We explicitly penalized this shortcut and verified that our model relies on holistic syntactic context rather than verbatim keyword memorization."

---

### Slide 18: Speaker-Disjoint Cross-Validation & Slice Disparities
- **Slide Title:** Speaker-Disjoint Cross-Validation & Slice Disparities
- **Visual Focal Point:** Left: Speaker shortcut bias (Cramér's $V=0.48$), 25-fold speaker-disjoint CV ($57.1\% \pm 10.0\%$), slice disparities. Right: Fig 7 (Speaker ablation and slice chart).

#### Verbatim Presenter Script:
> "One of our most critical discoveries was speaker shortcut bias. Because each student speaker recorded one or two intent types, a naive classifier recognizing speaker voice identity alone scored 41.3% accuracy, with a Cramér's V correlation of 0.48! Standard random cross-validation produced an artificially inflated 75%.
>
> To defeat this shortcut, we implemented strict 25-fold Speaker-Disjoint Cross-Validation using StratifiedGroupKFold. This yielded an honest, uncorrupted cross-validation score of 57.1% ± 10.0%, perfectly aligning with our 60.0% unseen release test score.
>
> Fine-grained slice analysis confirmed that hostel environments score 41.7% versus 16.7% in noisy canteens, and English queries reach 89% versus 29% in regional Gujarati."

---

### Slide 19: 20-Error Taxonomy & Model Card Specifications
- **Slide Title:** 20-Error Taxonomy & Model Card Specifications
- **Visual Focal Point:** Left: Categorized error distribution (Topic Drift 35%, Script Collapse 25%, Boundary Clipping 20%, Dialectal Substitution 15%, Near-Silent 5%) and Model Card. Right: Fig 8 (Error distribution).

#### Verbatim Presenter Script:
> "We conducted a manual root-cause audit of 20 test classification failures and formalized them into five distinct error modes:
> Topic drift accounted for 35% of errors, script mixing 25%, boundary noise clipping 20%, dialectal substitution 15%, and near-silent audio 5%. For each error mode, we engineered a specific mitigation.
>
> We also published a comprehensive Model Card in `MODEL_CARD.md`, explicitly declaring that this system is designed solely for campus administrative triage and must never be deployed for emergency dispatch."

---

### Slide 20: Section Divider: Part D: Offline Docker Deployment & User Interface
- **Slide Title:** Part D: Offline Docker Deployment & User Interface
- **Visual Focal Point:** Section header box.

#### Verbatim Presenter Script:
> "In Part D, we transition to software engineering and deployment: containerizing the entire system for local CPU serving and building interactive user interfaces."

---

### Slide 21: Self-Contained Offline Docker Service (`linux/amd64`)
- **Slide Title:** Self-Contained Offline Docker Service (`linux/amd64`)
- **Visual Focal Point:** Left: Container architecture, 1.97 GB footprint, peak RSS 649 MiB, single-command entrypoints. Right: Fig 9 (Docker validation run under `--network none`).

#### Verbatim Presenter Script:
> "Our Docker container is engineered strictly for `linux/amd64` commodity CPU hardware, built from `python:3.10-slim`.
> The final image is 1.97 GB, and during active inference, peak RSS reaches just 649 MiB—well below the 4.2 GB platform limit.
>
> All model weights are baked into the image at `/opt/models`, with `HF_HUB_OFFLINE=1` enforced.
>
> We provide two single-command entrypoints: `serve` launches the interactive UI, while `validate` executes our 40-clip test harness under strict `--network none` isolation, proving zero reliance on external network downloads."

---

### Slide 22: Interactive Streamlit UI & Production FastAPI Microservice
- **Slide Title:** Interactive Streamlit UI & Production FastAPI Microservice
- **Visual Focal Point:** Left: Streamlit UI features, FastAPI endpoints (`/predict`, `/health`, `/version`), CPU latency benchmarks. Right: Fig 10 (Streamlit live screenshot).

#### Verbatim Presenter Script:
> "For user interaction, we developed both a production REST microservice and a Streamlit front-end.
> The Streamlit interface supports live microphone recording, file uploads, and pre-bundled consented clips across all four departments. It displays real-time verbatim transcripts, predicted intents, confidence gauges, and active Git commit tags.
>
> The FastAPI service exposes `POST /predict`, processing audio queries in approximately 300 milliseconds on CPU, along with health telemetry endpoints and non-PII logging."

---

### Slide 23: Section Divider: Part E: Online Monitoring, Drift & Gated Retraining
- **Slide Title:** Part E: Online Monitoring, Drift & Gated Retraining
- **Visual Focal Point:** Section header box.

#### Verbatim Presenter Script:
> "In Part E, we address operational MLOps: monitoring live traffic, detecting accent drift, and executing safety-gated retraining."

---

### Slide 24: Multi-Signal Online Monitoring Architecture
- **Slide Title:** Multi-Signal Online Monitoring Architecture
- **Visual Focal Point:** Left: Predictive softmax entropy $H(y|x)$, audio SNR tracking, script ratio. Right: Fig 11 (Telemetry dashboard: entropy vs accuracy).

#### Verbatim Presenter Script:
> "In production, ground-truth labels are unavailable at inference time. Therefore, we monitor three complementary unsupervised telemetry signals:
> First and foremost, Predictive Softmax Entropy: $H(\hat{y}|x) = -\sum p_c \log p_c$. Confident in-domain predictions exhibit low entropy around 0.82. When shifted queries arrive, output distributions flatten, driving entropy above our adaptive threshold of 1.15.
>
> Second, audio SNR tracking detects microphone degradation.
> Third, script ratio monitoring flags unexpected token distributions.
> As shown in Fig 11, entropy serves as an immediate, label-free proxy for model accuracy."

---

### Slide 25: Streaming Traffic Replay & Distribution Shift
- **Slide Title:** Streaming Traffic Replay & Distribution Shift
- **Visual Focal Point:** Left: 6-batch streaming simulation, Cohort B Maharashtra accent injection, Batch 6 drift alert. Right: Fig 12 (Replay telemetry: decoder log-prob vs Hindi share).

#### Verbatim Presenter Script:
> "To test our monitoring system, we simulated live traffic using a 6-batch replay harness:
> Batches 1 through 4 replay standard in-domain campus queries, maintaining stable entropy around 0.82 and 65% accuracy.
>
> In Batches 5 and 6, we injected shifted Cohort B queries—featuring Maharashtra accents and regional vocabulary.
> At Batch 6, predictive entropy spikes to 1.24, crossing the 1.15 threshold and automatically firing a high-priority drift alert to trigger retraining."

---

### Slide 26: Active Retraining & Strict Safety Promotion Gates
- **Slide Title:** Active Retraining & Strict Safety Promotion Gates
- **Visual Focal Point:** Left: Two-stage safety gates (Cohort B gain $\ge +5\%$, Gold degradation $\le 2\%$), Scenario A vs Scenario B empirical test. Right: Fig 13 (Promotion gate: adaptation vs catastrophic forgetting).

#### Verbatim Presenter Script:
> "When the drift alert fires, our active retraining pipeline selects the 10 lowest-confidence adaptation clips.
> However, newly trained models must pass two non-negotiable safety gates before deployment:
> Gate 1 requires at least a 5% gain on the new drift cohort. Gate 2 strictly prohibits more than a 2% drop on the original Gold test set.
>
> Here we demonstrated a textbook case of Catastrophic Forgetting:
> In Scenario A, retraining directly on drift clips boosted Cohort B accuracy by 14.2%, passing Gate 1. But core Gold accuracy plummeted from 62.5% down to 30.0%—a catastrophic 32.5% collapse!
>
> Our rigid safety gate immediately caught the failure, blocked deployment, and executed an automated rollback to the production champion."

#### Anticipated Professor Question & Defense:
- **Q:** *Why did Scenario B (Rehearsal Blend) also get rejected?*
- **A:** *In Scenario B, blending 77 base clips with 10 drift clips was insufficient to overcome the domain shift ($\Delta = 0.0\%$ gain on Cohort B), while still causing a 12.5% drop on Gold. This proves that naive fine-tuning without parameter-efficient adapter layers (like LoRA) is prone to negative transfer, justifying our strict promotion gate.*

---

### Slide 27: Section Divider: Parts F & G: Reproducibility, Contributions & Live Demo
- **Slide Title:** Parts F & G: Reproducibility, Contributions & Live Demo
- **Visual Focal Point:** Section header box.

#### Verbatim Presenter Script:
> "Finally, let us review our reproduction protocol, technical contributions, and scientific insights."

---

### Slide 28: 5-Command Exact Reproduction Protocol
- **Slide Title:** 5-Command Exact Reproduction Protocol
- **Visual Focal Point:** Exact terminal commands, SHA-256 cryptographic checksums, tagged repository release `a2-final`.

#### Verbatim Presenter Script:
> "Full scientific reproducibility is guaranteed in five deterministic terminal commands:
> Checking out git tag `a2-final`, installing pinned dependencies, pulling DVC data, running `train.py`, and evaluating on the gold split.
>
> Every evaluation run cryptographically asserts the SHA-256 hash of `gold_test_set.csv`, logging every access in `TEST_SET_LOG.md`. Fixed seed 42 is enforced across all operations."

---

### Slide 29: Equal Technical Contribution Breakdown (33.3% Each)
- **Slide Title:** Equal Technical Contribution Breakdown (33.3% Each)
- **Visual Focal Point:** Structured table detailing Rajdeep Vraj (22110215), Vipul Sunil Patil (22110189), and Satvik Sharma (26120008).

#### Verbatim Presenter Script:
> "All three team members contributed equally—exactly 33.3% each—across all phases of the project:
> Rajdeep led the baseline models, Whisper decoding integration, augmentation ablation, and the 1,000 bootstrap CI evaluation engine.
>
> Vipul led dual MLflow and Weights & Biases experiment tracking, model registry aliases, the FastAPI microservice, Streamlit UI, and offline Docker packaging.
>
> Satvik led online telemetry, streaming traffic replay, closed-loop retraining pipelines, safety promotion gating, and the 20-error taxonomy."

---

### Slide 30: Conclusions, Scientific Insights & Future Roadmap
- **Slide Title:** Conclusions, Scientific Insights & Future Roadmap
- **Visual Focal Point:** Five core technical achievements and future engineering roadmap.

#### Verbatim Presenter Script:
> "To conclude, this project delivered five major technical achievements:
> First, a complete, privacy-compliant voice helpdesk operating on commodity CPU edge hardware with a Real-Time Factor of 0.17.
> Second, uncompromising academic honesty in auditing and exposing speaker shortcut bias and template leakage.
> Third, 60.0% accuracy on unseen test speakers against a 25% chance baseline.
> Fourth, tripling Gujarati routing accuracy to 71% via acoustic LID logits.
> And fifth, an automated safety gate that successfully caught and blocked catastrophic forgetting in production.
>
> For future work, we look forward to parameter-efficient LoRA fine-tuning and expanded multi-epoch continual learning."

---

### Slide 31: References and Live Demonstration / Thank You
- **Slide Title:** References and Live Demonstration
- **Visual Focal Point:** Core scientific literature citations, 3-minute demonstration screencast reference, GitHub repository URL.

#### Verbatim Presenter Script:
> "Our work builds upon seminal research in speech recognition, experiment tracking, and bootstrap statistics by Radford, Zaharia, Efron, and McNemar.
>
> Our complete submission includes a 3-minute screen recording verifying offline Docker execution under `--network none`, live Streamlit triage, and the Batch 6 drift alert and rollback.
>
> Thank you for your time and guidance throughout this course. We are now open for your questions."
