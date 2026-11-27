# Technical Decisions & Rationales Guide

This document summarizes the core technical, architectural, and methodological decisions made during the design, development, and deployment of the Voice Helpdesk system, detailing the rationale, constraints, and empirical evidence behind each choice.

---

## 1. Decoupled ASR + Lightweight Intent Head (vs. End-to-End Speech-to-Intent)
- **Decision:** Use a frozen Whisper-base acoustic feature extractor / greedy text decoder coupled with a lightweight MLP routing head, rather than fine-tuning an end-to-end multi-modal Transformer.
- **Basis & Rationale:**
  1. *Resource Constraints:* The project enforces strict offline deployment on standard commodity CPU hardware with a **<4.2 GB RAM ceiling** (achieved: **649 MiB peak RSS**).
  2. *Inference Latency:* Real-Time Factor (RTF) is $\approx 0.17$ ($\sim 300$\,ms per 5s audio clip) on CPU. Fine-tuning end-to-end models on CPU would make real-time interaction impossible.
  3. *Modular Auditability:* Decoupling allows independent auditing and debugging of acoustic ASR transcription errors (WER) versus semantic triage classification errors (F1).

---

## 2. Hybrid Text Representations: Sublinear TF-IDF + Frozen MiniLM Embeddings
- **Decision:** Concatenate sublinear word/character n-grams ($n \in [1, 3]$) with 384-dimensional dense semantic embeddings from frozen `all-MiniLM-L6-v2`.
- **Basis & Rationale:**
  1. *Campus-Specific Lexicon:* Dense sentence transformers frequently fail on rare, campus-specific abbreviations and acronyms ("SPI", "CPI", "mess rebate", "grade card", "bonafide certificate"). Character and word n-gram TF-IDF provides exact lexical matching.
  2. *Semantic Generalization:* Dense embeddings capture syntactic paraphrasing and multilingual cross-lingual intent when exact keywords are missing.
  3. *Sublinear Damping:* Sublinear scaling ($\text{TF} = 1 + \log(\text{tf})$) dampens repetitive conversational fillers ("sir", "please", "actually", "basically") from dominating feature weights.

---

## 3. 40-Word Window Normalization Truncation
- **Decision:** Truncate transcript decoding to the opening 40 words for intent classification.
- **Basis & Rationale:**
  1. *Root Cause Error Analysis:* Auditing 20 test failure modes revealed that **35% of all misclassifications** were caused by conversational preamble and mid-query topic drift (e.g., student discusses hostel life for 15 seconds before asking an academic fee question).
  2. *Empirical Validation:* Extracting the first 40 words captures the primary administrative intent with minimal noise, improving cross-validation accuracy from $55.2\%$ to **$57.1\%$**.

---

## 4. 25-Fold Speaker-Disjoint Cross-Validation (vs. Random K-Fold)
- **Decision:** Enforce strict speaker-disjoint cross-validation (`StratifiedGroupKFold`) grouped by speaker ID.
- **Basis & Rationale:**
  1. *Speaker Shortcut Bias Discovery:* Statistical audit revealed a strong association between student speakers and intents (Cramér's $V = 0.48$). A trivial classifier trained on speaker voice identity alone achieved **41.3% intent accuracy** without listening to the spoken query!
  2. *Leakage Prevention:* Standard random K-fold splits yielded an artificially inflated $75\%$ accuracy due to memorizing speaker acoustics. Speaker-disjoint CV eliminated acoustic leakage, producing an honest, verifiable unseen baseline ($57.1\% \pm 10.0\%$).

---

## 5. Withdrawing Curated Transcripts & Conducting Genuine Round T
- **Decision:** Formally withdraw original curated reference transcripts and conduct a clean, from-scratch human transcription round (**Round T**).
- **Basis & Rationale:**
  1. *Transcription Speed Audit:* Curated references exhibited an unnatural median typing rate of 1.2 words per second, indicating annotators were writing idealized script templates rather than verbatim acoustic speech.
  2. *Verifiable Human Baseline:* Round T gathered 174 human-transcribed clips (76 double-annotated), proving human inter-annotator WER is $31.8\%$--$34.2\%$ and establishing an authentic acoustic benchmark ($0.51$ Whisper WER).

---

## 6. Learned 99-Dimensional Language Identification (LID) Router
- **Decision:** Extract the 99-dimensional language logit probability vector from the Whisper encoder and concatenate it with text features for low-resource languages.
- **Basis & Rationale:**
  1. *Low-Resource Language Collapse:* In raw text decoding, code-mixed Gujarati queries often collapsed into phonetically similar Devanagari/Hindi tokens, yielding a dismal 24% routing accuracy.
  2. *Acoustic Routing:* Feeding Whisper's acoustic LID distribution directly into the MLP classifier enabled the model to recognize Gujarati queries acoustically, **tripling Gujarati accuracy from 24% to 71%**.

---

## 7. Dual MLOps Tracking: MLflow + Weights & Biases (W&B) Parity
- **Decision:** Track all 15 hyperparameter search runs simultaneously in both local **MLflow** (`mlruns/`, `mlflow.db`) and cloud **Weights & Biases** (`voice-helpdesk-asr`).
- **Basis & Rationale:**
  1. *Zero Vendor Lock-In & Portability:* Local MLflow enables complete offline operation and air-gapped reproducibility on test machines.
  2. *Rich Visualization:* Weights & Biases provides live validation learning curves, parameter importance correlations, and shareable dashboards.
  3. *Independent Champion Verification:* Both systems independently identified Run 6 (`9820a2a7`) as the Pareto champion (52.9% val acc, 0.007 ms latency, 105.5 KB size).

---

## 8. Unsupervised Softmax Entropy as Primary Drift Telemetry Signal
- **Decision:** Use predictive softmax entropy $H(\hat{y}|x) = -\sum_{c} p_c \log p_c$ for real-time online monitoring rather than waiting for ground-truth user feedback.
- **Basis & Rationale:**
  1. *Label-Free Production Serving:* In a live voice helpdesk, ground-truth labels do not exist at inference time. Telemetry must be completely unsupervised.
  2. *Predictive Correlation with Failure:* In-domain queries exhibit sharp, confident probabilities (mean entropy $H \approx 0.82$). As distribution shift occurs (Cohort B Maharashtra accent and colloquial Marathi terms), the model becomes uncertain, driving entropy past the $1.15$ threshold ($H=1.24$), reliably signaling drift before silent failures accumulate.

---

## 9. Rigid $\le 2.0\%$ Gold Set Degradation Gate (Catastrophic Forgetting Defense)
- **Decision:** Impose a non-negotiable two-stage promotion gate for any candidate model retrained on drifted traffic:
  - Gate 1: Drift set (Cohort B) accuracy must improve by $\ge \mathbf{+5.0\%}$.
  - Gate 2: Original Gold test set accuracy must not degrade by more than $\mathbf{\le 2.0\%}$ ($\le 1$ clip drop out of 40).
- **Basis & Rationale:**
  1. *Empirical Demonstration of Catastrophic Forgetting:* Retraining directly on new drift clips increased Cohort B accuracy from $42.9\%$ to $57.1\%$ ($+14.2\%$), but catastrophically damaged core Gold accuracy, which plummeted from **$62.5\%$ down to $30.0\%$** ($-32.5\%$).
  2. *Automated Governance:* A system that learns new accents at the expense of its core campus vocabulary is dangerous. The $\le 2.0\%$ threshold immediately caught the collapse, rejected the candidate model, and executed an automatic rollback to the verified production champion.

---

## 10. Self-Contained Offline Docker Packaging (`--network none`)
- **Decision:** Package the entire FastAPI service, Streamlit UI, model weights, and validation harnesses into a single self-contained Docker image (`linux/amd64`, 1.97 GB) verified under `--network none`.
- **Basis & Rationale:**
  1. *Privacy & Institutional Compliance:* Spoken student administrative queries (financial aid, grades, disciplinary records) must never leak to third-party cloud APIs.
  2. *Audit Verification:* Running `docker run --network none <image> validate` provides absolute proof to evaluators and professors that all weights, tokenizers, and dependencies are locally bundled and run with zero external network connectivity.
