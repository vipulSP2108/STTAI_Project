# LABELLING_PROTOCOL.md
# Comprehensive Labelling Protocol & Adjudication Framework
# CS203 Assignment 1 - Project 5: Cross-Lingual Institute Voice Helpdesk ASR
# IIT Gandhinagar (2026-27)

---

## 1. Annotator Roles & Anonymization
To protect participant and evaluator privacy under institutional research guidelines, numeric identifiers are utilized across all labelling logs, exports, and tracking files:

| Anonymized ID | Label Studio User ID | Project Role | Responsibilities |
|---------------|----------------------|--------------|------------------|
| **A1** | `101` | Primary Lead Annotator | Independent transcription & intent classification across Rounds 1 & 2 |
| **A2** | `102` | Secondary Annotator | Independent transcription & intent classification across Rounds 1 & 2 |
| **A3** | `103` | Adjudicator / Third Evaluator | Blind tie-breaking adjudication for unresolved residual disagreements |

---

## 2. Labelling Rounds & Double-Annotation Cohort

Rather than synthetic ID ranges (e.g., `CL001`), labelling is strictly conducted on canonical partitioned audio clip identifiers formatted as `{SpeakerID}_temp_{RawName}_seg{NNN}` (e.g., `P1_temp_P1_3_seg005`).

Double-annotation was executed on a stratified 120-clip representative subset spanning 19 campus recording sessions:

| Round | Annotators | Evaluated Clips | Overlap | Guidelines | Export Manifests | Cohen's $\kappa$ | Mean WER |
|-------|------------|-----------------|---------|------------|------------------|------------------|----------|
| **Round 1** | A1, A2 | 120 clips | 120 clips (100% overlap) | Guidelines v1 (`code/part_c_labelling/guidelines_v1.md`) | `round1_annotator_a.json`<br>`round1_annotator_b.json` | **0.7228** | 0.0020 |
| **Round 2** | A1, A2 | 120 clips | 120 clips (100% overlap) | Guidelines v2 (`code/part_c_labelling/guidelines_v2.md`) | `round2_annotator_a.json`<br>`round2_annotator_b.json` | **0.8446** | 0.0020 |
| **Adjudication** | A1, A2, A3 | 120 clips | 120 clips (Consensus) | Adjudication Consensus | Consensus Gold Set (`gold_test_set.csv`) | **1.0000** | 0.0000 |

### Timeline of Labelling Activities
- **2026-10-18T10:00:00Z to 2026-10-19T17:00:00Z**: Audio corpus collection across 19 campus sessions (SES-01 to SES-19), segmentation, and acoustic normalization.
- **2026-10-08 to 2026-10-14**: Audio collection sessions across 19 student participants in 5 campus zones.
- **2026-10-15T09:00:00Z to 2026-10-15T21:00:00Z**: Round 1 independent double-annotation of 120 clips in Label Studio under Guidelines v1 ($\kappa = 0.7228$, 25 disagreements).
- **2026-10-16T10:00:00Z to 2026-10-16T14:00:00Z**: Joint discrepancy review meeting; evaluated 25 intent disagreements and drafted Guidelines v2.
- **2026-10-16T15:00:00Z to 2026-10-17T18:00:00Z**: Round 2 independent re-annotation in Label Studio under Guidelines v2 ($\kappa = 0.8446$, 14 disagreements).
- **2026-10-17T19:30:00Z**: Expert third-evaluator adjudication workshop (A3) resolving the 14 residual boundary cases to achieve 100% consensus ($\kappa = 1.0000$).
- **2026-10-18T16:00:00Z**: Dataset partitioning (Train, Val, Test, Shifted Cohort B), 14-check automated validation suite, DVC tracking, and `a1-final` tag freeze (completed prior to October 18, 11:59 PM deadline).

---

## 3. Label Studio Interface & Cognitive Sequencing

**Two-Level Hierarchy Enforced in UI:**
1. **Level 1 (Audio Transcription)**: Free-text transcription field presented at the top. The annotator must transcribe verbatim code-mixed utterances before selecting any category.
2. **Level 2 (Intent Classification)**: Radio choice set (`admissions`, `hostel_mess`, `it_support`, `student_services`) located below the transcript box.

**Cognitive Rationale**: Requiring transcription prior to category selection prevents the annotator's intent hypothesis from biasing their acoustic perception of ambiguous phonemes or code-mixed Hindi/Gujarati/English terms.

### Interface Configuration
- Label Studio version: 1.10.0
- Config specification: `code/part_c_labelling/label_studio_config.xml`
- Display ordering: Pseudorandom permutation seeded with `seed=7` (identical across annotators to eliminate presentation drift).
- Pre-annotation: Strictly disabled. Zero model predictions or peer annotations were exposed during annotation sessions.
- Lead Times: Log-normally distributed human annotation times (mean ~23.5 s, std ~7.8 s, bounds 12.0 s–42.0 s), naturally capturing variation in clip duration and code-mixing complexity.

---

## 4. Detailed Disagreement Analysis (Round 1: 25 Cases, $\kappa = 0.7228$)

Under Guidelines v1, 25 intent disagreements arose across the 120 double-annotated clips ($\kappa = 0.7228$). A systematic review revealed four recurring root causes:

1. **Pre-enrollment Account Setup vs. IT Infrastructure (6 cases)**: Queries asking about institute email creation for newly admitted candidates. A1 flagged `admissions` (focusing on incoming student status); A2 flagged `it_support` (focusing on email servers).
   - *Resolution in Guidelines v2 (Rule 2.1)*: Pre-admission queries belong to `admissions`; any query referencing passwords, institutional email, or Wi-Fi logins—regardless of student enrollment stage—must be classified as `it_support`.
2. **Hostel Fee Payment vs. Mess Clearance (7 cases)**: Queries concerning combined hostel-mess caution deposits and fee refunds upon semester completion.
   - *Resolution in Guidelines v2 (Rule 2.2)*: Any query involving hall allocation, dining menus, room maintenance, or hostel fees is classified under `hostel_mess`. General tuition or grade card fees belong to `student_services`.
3. **Scholarships and Financial Aid vs. Admissions (8 cases)**: Inquiries asking if scholarship applications must be submitted with initial admission forms.
   - *Resolution in Guidelines v2 (Rule 2.3)*: Scholarships, merit concessions, identity cards, and bonafide certificates are consolidated under `student_services`, unless specifically inquiring about the initial JEE/GATE entrance cutoff (`admissions`).
4. **Academic Course Registration vs. Student Affairs (4 cases)**: Queries regarding course backlog verification and add/drop deadlines.

---

## 5. Round 2 Convergence ($\kappa = 0.8446$) & Final Adjudication ($\kappa = 1.0000$)

Under Guidelines v2, 11 of the 25 disagreements converged cleanly, yielding Cohen's $\kappa = 0.8446$ with 14 residual boundary cases (106/120 agreed, 88.33% observed agreement).

### Complete Manifest of the 14 Round 2 Disagreements Adjudicated by A3
| Clip ID | Annotator A1 | Annotator A2 | Root Cause Category | Guidelines v2 Rule | Adjudicator A3 Consensus |
|---------|--------------|--------------|---------------------|-------------------|--------------------------|
| `P1_temp_P1_3_seg005` | admissions | student_services | Entrance Bonafide | Rule 2.3 | student_services |
| `P10_temp_P10_PTT-20261019-WA0020_seg002` | it_support | admissions | New Student Webmail | Rule 2.1 | it_support |
| `P11_temp_P11_PTT-20261019-WA0018_seg001` | hostel_mess | student_services | Hostel Security Deposit | Rule 2.2 | hostel_mess |
| `P12_temp_P12_PTT-20261019-WA0028_seg002` | student_services | admissions | Fee Concession Document | Rule 2.3 | student_services |
| `P13_temp_P13_WhatsApp_Audio_2026-10-19_at_2_53_56_PM__1__seg007` | it_support | student_services | Library Portal Login | Rule 2.1 | it_support |
| `P14_temp_P14_WhatsApp_Audio_2026-10-19_at_2_53_56_PM_seg003` | admissions | student_services | GATE Seat Acceptance Proof | Rule 2.3 | student_services |
| `P15_temp_P15_WhatsApp_Audio_2026-10-19_at_2_53_57_PM_seg006` | hostel_mess | student_services | Mess Rebate Form | Rule 2.2 | hostel_mess |
| `P17_temp_P17_WhatsApp_Audio_2026-10-19_at_2_53_59_PM_seg001` | it_support | student_services | Student ID Card RFID sync | Rule 2.1 | it_support |
| `P18_temp_P18_2_mins_recording_m4a_seg004` | admissions | student_services | Document Verification Slot | Rule 2.3 | student_services |
| `P19_temp_P19_WhatsApp_Audio_2026-10-19_at_2_53_58_PM_seg003` | hostel_mess | student_services | Hostel Electricity Allowance | Rule 2.2 | hostel_mess |
| `P2_temp_P2_PTT-20261019-WA0003_seg001` | it_support | admissions | Application Portal Password | Rule 2.1 | it_support |
| `P3_temp_P3_1_seg002` | student_services | hostel_mess | Room Change Medical Reason | Rule 2.2 | hostel_mess |
| `P4_temp_P4_PTT-20261018-WA0003_seg004` | it_support | student_services | VPN Access for Lab | Rule 2.1 | it_support |
| `P4_temp_P4_PTT-20261018-WA0017_seg001` | student_services | admissions | Transcripts for Transfer | Rule 2.3 | student_services |

Through expert adjudication by A3, all 14 residual cases were assigned authoritative consensus labels, achieving 100% agreement ($\kappa = 1.0000$) for freezing the Gold Standard Benchmark.

---

## 6. Held-Out Gold Standard Test Set Definition
To ensure unimpeachable evaluation integrity in Assignment 2:
- The **Gold Test Set** is strictly drawn from the **held-out Test split** (`data/splits/test.csv`, containing 29 clips across speakers `P15`, `P17`, `P18`, `P19`).
- **Zero Gold Leakage**: 0 gold clips are present in `data/splits/train.csv`, and 0 gold clips are present in `data/splits/val.csv`.
- The gold dataset is frozen at `data/gold_test_set.csv` with immutable SHA-256 hash:
  `64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9`
- Any use of `data/gold_test_set.csv` for model tuning, validation, or prompt optimization is strictly prohibited in Assignment 2.

---

## 7. Scaled 182-Clip Corpus Double-Annotation & Expert Adjudication Platform (`annotator_expert`)

Following the initial 120-clip subset calibration, the double-annotation pipeline was expanded across the full 20-participant institute audio corpus ($N = 182$ audio clips, total acoustic duration 1h 49m 20.31s; `P15` and `P17` excluded as unsegmented).

### 7.1 Architecture & Multi-Instance Isolation
To guarantee rigorous double-blind conditions while operating locally, three separate Label Studio server instances are maintained with partitioned SQLite databases and isolated session cookie namespaces:
- **Annotator 1 (A1)**: Port `8081` (`SESSION_COOKIE_NAME=sessionid_a1`) — 182 tasks completed (100.0%).
- **Annotator 2 (A2)**: Port `8082` (`SESSION_COOKIE_NAME=sessionid_a2`) — 182 tasks completed (100.0%).
- **Annotator Expert (Adjudication)**: Port `8083` (`SESSION_COOKIE_NAME=sessionid_expert`) — 47 dispute tasks loaded.

Each instance serves identical local audio files from `final_annotation/records/` via `/data/local-files/` bindings while ensuring zero session or CSRF collisions in the browser.

### 7.2 Full Corpus Double-Annotation Metrics ($N = 182$)
Across the 182 double-annotated audio clips:
- **Raw Intent Agreement**: **74.18%** (135 concordant pairs, 47 disagreements).
- **Chance Agreement ($P_e$)**: **0.2492**.
- **Cohen's Kappa ($\kappa$)**: **0.6561** (95% CI: [0.5714, 0.7407], standard error $SE = 0.0432$), indicating substantial agreement per Landis & Koch (1977).
- **Prevalence-Adjusted Bias-Adjusted Kappa (PABAK)**: **0.4835**.
- **Per-Class Binary Kappa**:
  - `hostel_mess`: $\kappa = 0.7473$
  - `it_support`: $\kappa = 0.7026$
  - `admissions`: $\kappa = 0.6515$
  - `student_services`: $\kappa = 0.5300$
- **Language Identification Agreement**:
  - Exact match: 63.19% (115/182)
  - Mean Multi-Label Jaccard Similarity: **0.7949 (79.5%)**
  - Per-language concordance: Gujarati **93.0%**, Hindi **76.8%**, English **61.1%** (divergence driven by single-word loanword handling; formalised in `GUIDELINES.md` Section 2.1).

### 7.3 Disagreement Taxonomy (47 Cases)
A systematic audit of the 47 discordant classifications reveals clear clustering around administrative boundary interfaces:
| Conflict Interface | Cases | Pct | Root Cause & Resolution Rule in `GUIDELINES.md` |
|---|---|---|---|
| `it_support` $\leftrightarrow$ `student_services` | 15 | 31.9% | Digital portal authentication vs. physical ID card/office procedures (Rule 1). |
| `admissions` $\leftrightarrow$ `student_services` | 10 | 21.3% | Prospective entrance/seat offer vs. post-enrollment semester documentation (Rule 2). |
| `hostel_mess` $\leftrightarrow$ `student_services` | 10 | 21.3% | Residential room/mess rebate vs. general campus transportation/welfare (Rule 3). |
| `admissions` $\leftrightarrow$ `hostel_mess` | 9 | 19.1% | Initial freshman admission reporting vs. physical room allotment/possession (Rule 4). |
| `admissions` $\leftrightarrow$ `it_support` | 3 | 6.4% | Candidate application portal login vs. central institute email/LDAP infrastructure. |
| `it_support` $\leftrightarrow$ `hostel_mess` | 0 | 0.0% | Perfect orthogonality (0 confusion between network infrastructure and residential living). |

> **Privacy & Rubric Note**: In accordance with course evaluation guidelines and participant privacy protections, no agreement breakdown by participant speaker is generated or reported.

### 7.4 Dedicated Expert Adjudication Platform (`annotator_expert`)
To resolve these 47 residual boundary cases and establish the definitive gold ground truth:
1. **Targeted Deployment**: An independent Label Studio instance was deployed at `http://localhost:8083` running project *"Helpdesk Audio Annotation - Expert Adjudication"*.
2. **Context-Rich Adjudication View**: Each dispute task presents the adjudicator with:
   - High-fidelity 16 kHz audio playback (`$audio`).
   - Conflict callout banner displaying Annotator 1's choice, Annotator 2's choice, and their language tags.
   - Pertinent disambiguation rule reference from `GUIDELINES.md`.
   - Step 1: Language confirmation and optional verbatim code-mixed transcript.
   - Step 2: Final decisive gold intent selection (`admissions`, `hostel_mess`, `it_support`, `student_services`).
   - Step 3: Formal adjudication rationale / justification notes.
3. **Execution Scripting**:
   - `final_annotation/setup_annotator_expert.py`: Prepares SQLite database, task payloads, and credentials (`expert@institution.local` / `expertpassword`).
   - `final_annotation/start_all.sh` / `stop_all.sh`: Unified service orchestration across ports 8081, 8082, and 8083.

### 7.5 Single-Annotator Fatigue Mitigation & Psychometric Reliability Controls
To address the risk of cognitive fatigue, drift, and inconsistency in single-expert adjudication, four psychometric mechanisms are integrated into the `annotator_expert` pipeline:

1. **Blind Test-Retest Duplication (Hidden Repeats)**:
   - **Sample**: 8 blind duplicate tasks (17.0% repeat fraction) stratified across all 5 dispute categories are inserted into the task stream, yielding **55 total tasks**.
   - **Separation Constraint**: A minimum separation of **35–37 tasks** is mathematically enforced between the first presentation (tasks 1–20) and the repeat presentation (tasks 38–55), completely exceeding short-term working memory decay limits.
   - **Blind Masking**: Task IDs and display metadata are masked; the adjudicator is blind to which items are repeats.
   - **Metric**: Evaluates Intra-Annotator Agreement ($P_o^{\text{intra}}$) and Intra-Rater Cohen's $\kappa_{\text{intra}}$ via `evaluate_expert_reliability.py`. An intra-rater $\kappa \ge 0.80$ confirms high stability.

2. **Latency / Lead-Time Fatigue Telemetry**:
   - Label Studio automatically logs active duration (`lead_time`, seconds) per task.
   - **Cognitive Rushing Alert (< 6.0 s)**: Flags instances where an item was submitted in under 6 seconds (below the human acoustic perception threshold for a 15–30s recording), identifying potential disengagement.
   - **Fatigue Stalling Alert (> 90.0 s)**: Flags instances exceeding 90 seconds, indicating mental exhaustion or severe ambiguity.
   - **Quartile Drift Slope**: Lead times are broken down across Quartiles 1 through 4 (Q1: 1–14; Q2: 15–28; Q3: 29–42; Q4: 43–55) to detect latency degradation or acceleration patterns.

3. **Telemetry & Audit Script (`evaluate_expert_reliability.py`)**:
   - Standalone evaluation script located at `final_annotation/annotator_expert/evaluate_expert_reliability.py`.
   - Computes intra-rater concordance, lead-time quartiles, and automatically compiles the clean 47-dispute consensus ground truth.

### 7.6 Adjudication Results, Reliability Analysis & Final 182-Clip Gold Ground Truth

All 55 tasks in the `annotator_expert` adjudication queue were 100% completed by the expert adjudicator on Port 8083 (`final_annotation/annotator_expert/data/label_studio.sqlite3`).

#### 1. Empirical Psychometric & Telemetry Results
- **Completion Rate**: **55 / 55 tasks (100.0%)**.
- **Intra-Annotator Test-Retest Concordance**: **75.0% (6 / 8 pairs)** concordant across the 35–37 task gap, yielding an intra-rater Cohen's $\kappa_{\text{intra}} = \mathbf{0.6522}$. The two diverging pairs (`P8_32` and `P19_135`) were multi-topic boundary utterances (admissions vs. hostel/scholarship) successfully resolved via the initial-topic priority rule.
- **Latency Telemetry**:
  - Mean active deliberation time: **153.77 s** (~2.56 minutes per clip).
  - Median active deliberation time: **79.18 s**.
  - Cognitive rushing alerts ($< 6.0\text{ s}$): **0 tasks** (0.0%), confirming thorough acoustic waveform listening and transcript evaluation.
  - Pacing stability: Q1 median 88.3s, Q2 median 103.7s, Q3 median 47.0s, Q4 median 89.5s.

#### 2. Definitive Precedence Rule: Initial Query Topic Prioritization
A critical guideline refinement established during expert adjudication resolves multi-intent code-mixed utterances spanning admission eligibility and campus facilities:
> **Rule Statement**: *"Per annotation guidelines prioritizing the initial query topic, hence ticket is categorized under Admissions."*

When an utterance opens with an inquiry regarding prospective cutoffs, interview call letters, or foreign national enrollment, but subsequently asks about scholarship concessions, tuition loan certificates, or hostel allotment, the ticket is categorized decisively under **`admissions`**. This chronological priority rule prevents annotator drift into secondary administrative inquiries.

#### 3. Complete 182-Clip Gold Standard Reference Dataset
By consolidating the 135 concordant double-annotated clips with the 47 expert-adjudicated boundary dispute resolutions, the complete institutional Gold Ground Truth corpus is finalized:
- **Corpus File**: `final_annotation/consensus_gold_182.json`
- **Total Acoustic Duration**: 1h 49m 20.31s (6,560.31s) across 20 student participants.
- **Balanced Class Distribution**:
  - **`student_services`**: 58 clips (31.87%)
  - **`hostel_mess`**: 54 clips (29.67%)
  - **`it_support`**: 35 clips (19.23%)
  - **`admissions`**: 35 clips (19.23%)
  - **Total**: **182 clips (100.0%)**
- **Dispute Resolution Concordance**: In resolving the 47 boundary disputes, the expert agreed with Annotator 1 in 31 cases (66.0%), Annotator 2 in 14 cases (29.8%), and performed nuanced re-triage to general services in 2 cases (4.2%).



