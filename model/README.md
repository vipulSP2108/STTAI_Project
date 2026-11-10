# IIT Gandhinagar Multilingual Voice Helpdesk Model Pipeline

**Course**: CS203 Software Tools and Techniques in AI  
**Project**: Project 5 – Voice Helpdesk Multilingual System  
**Corpus**: 182 Audio Clips (Hindi, Gujarati, English, Code-Mixed) across 4 Intent Classes (`hostel_mess`, `student_services`, `it_support`, `admissions`).

---

## 1. Directory Structure

All model preparation, data sanitization, multilingual augmentation, and training workflows are centralized in this single directory:

```
model/
├── config.yaml                          # Master hyperparameters, thresholds, paths
├── requirements.txt                     # Pinned Python package dependencies
├── README.md                            # Operational and architectural guide
├── cli.py                               # Unified command-line interface
│
├── data/                                # Unified data directory
│   ├── raw/                             # Immutable source snapshot (consensus_gold_182.json)
│   ├── audio/                           # Model audio clips (<uuid>.wav)
│   ├── text/                            # Model text files (<uuid>.txt)
│   ├── augmented/                       # Validated augmented derivatives
│   │   ├── back_translation/
│   │   ├── pivot_latin/
│   │   ├── lexical_synsets/
│   │   ├── code_mixed/
│   │   └── audio_perturbed/
│   ├── metadata/                        # Provenance & auditing manifests
│   │   ├── internal_manifest.json       # SECRET: UUID -> Parent Clip, Speaker, Lineage
│   │   ├── dataset_summary.json         # High-level corpus statistics & class balance
│   │   └── augmented_manifest.json      # Lineage tracking for all accepted augmented variants
│   ├── splits/                          # Leakage-free StratifiedGroupKFold partitions
│   │   ├── fold_1.json .. fold_5.json
│   │   └── independent_test_set.json    # Held-out unseen student speaker benchmark
│   └── reports/                         # Automated validation & audit logs
│       ├── dataset_audit.json
│       ├── asr_transcription_report.json
│       ├── augmentation_quality_report.json
│       └── leakage_verification_report.json
│
├── src/                                 # Modular Python source code
│   ├── asr/                             # Stage 1: Offline Speech-to-Text
│   │   ├── transcribe.py                # Batch offline Whisper ASR engine
│   │   └── transcribe_worker.py         # Accelerated parallel ASR worker
│   ├── sanitization/                    # Stage 2: Feature Stripping & Randomization
│   │   └── uuid_packager.py             # Generates matching audio/<uuid>.wav & text/<uuid>.txt
│   ├── augmentation/                    # Stage 3: Multilingual Augmentation Engine
│   │   ├── back_translation.py          # Multilingual back-translator (Hindi/Gujarati <-> English)
│   │   ├── pivot_translator.py          # Latin/Romance pivot translation path
│   │   ├── lexical_synsets.py           # Domain synset substitution
│   │   ├── code_mix_generator.py        # Campus Gujarati/Hindi-English code-switching
│   │   ├── audio_augmenter.py           # Speed, pitch, and canteen noise injection
│   │   └── pipeline.py                  # Orchestrator with 3 Semantic Quality Gates
│   ├── validation/                      # Stage 4: Semantic Quality Gates
│   │   ├── embedding_filter.py          # Gate 1: CosineSim(v_orig, v_aug) >= 0.82
│   │   ├── polarity_checker.py          # Gate 2: Negation & Entity Invariance Auditor
│   │   └── deduplicator.py              # Gate 3: MinHash & N-gram Deduplicator
│   ├── splitting/                       # Stage 5: Leakage-Free StratifiedGroupKFold
│   │   ├── group_splitter.py            # StratifiedGroupKFold implementation
│   │   └── leakage_auditor.py           # Automated zero-leakage verification suite
│   ├── training/                        # Stage 6: Supervised Model Training
│   │   ├── dataset.py                   # PyTorch Dataset loader (zero administrative metadata)
│   │   ├── models.py                    # Calibrated Multilingual Classifier & Neural Heads
│   │   └── ablation_runner.py           # Orchestrates 10-configuration ablation study
│   └── evaluation/                      # Evaluation & Benchmarking
│       ├── evaluate.py                  # Macro-F1, per-class F1, confusion matrix
│       └── unseen_speaker_test.py       # Generalization on held-out student participants
│
├── models/                              # Serialized model weights & tokenizers
└── results/                             # Experiment outputs, tables, and plots
    ├── ablation_study_results.json
    └── unseen_speaker_benchmark.json
```

---

## 2. CLI Usage Reference

The complete system is operable via `python -m model.cli <subcommand>`:

```bash
# 1. Audit corpus health and class distribution
python -m model.cli audit

# 2. Run batch offline ASR transcription
python -m model.cli transcribe --model base

# 3. Strip metadata, assign UUIDs, and generate manifests
python -m model.cli sanitize

# 4. Generate multilingual augmentations and run 3 quality gates
python -m model.cli augment --threshold 0.82

# 5. Partition dataset into 5-Fold StratifiedGroupKFold splits
python -m model.cli split --folds 5

# 6. Verify zero data leakage across all folds
python -m model.cli verify

# 7. Execute the mandatory 10-configuration ablation study
python -m model.cli ablate

# 8. Benchmark on unseen student speakers and language slices
python -m model.cli benchmark
```

---

## 3. The 10-Configuration Ablation Study

| Config ID | Training Dataset Configuration | Hypothesis & Evaluated Technique |
|:---:|:---|:---|
| **C-01** | **Baseline (Raw Transcripts Only)** | Performance floor using only the 182 original transcripts. |
| **C-02** | Original + Back-Translation | Tests syntactic clause reordering via Hindi/Gujarati/English loops. |
| **C-03** | Original + Cross-Lingual Paraphrase | Evaluates direct syntactic transfer across campus languages. |
| **C-04** | Original + Pivot Translation (Latin) | Tests morphological abstraction via Romance/Latinate pivot transformation. |
| **C-05** | Original + Lexical Synonym Replacement | Evaluates domain synset expansion across administrative terms. |
| **C-06** | Original + Contextual MLM Substitution | Evaluates masked bidirectional contextual token replacement. |
| **C-07** | Original + Campus Code-Switching | Tests robustness to intra-sentential Gujarati/Hindi-English code switching. |
| **C-08** | Original + Acoustic Audio Perturbations | Tests acoustic feature variation (speed, pitch, ambient noise). |
| **C-09** | Original + Top-3 Synergistic Text Techniques | Evaluates synergistic combination of Back-Translation + Lexical Synsets + Code-Mixing. |
| **C-10** | **Complete Optimized Pipeline (All Gates Active)** | Full dataset combining all techniques passed through semantic similarity & deduplication gates. |

---

## 4. Leakage-Free Stratified Group Constraint

To prevent data leakage, all augmented derivatives and acoustic perturbations inherit the **exact same `split_group_id`** (`GRP_<speaker_id>_<clip_id>`) as their parent audio clip.
When partitioned with `StratifiedGroupKFold(n_splits=5)`:
- $\text{ParentIDs}(\text{Train}_k) \cap \text{ParentIDs}(\text{Val}_k) = \emptyset$
- $\text{SplitGroupIDs}(\text{Train}_k) \cap \text{SplitGroupIDs}(\text{Val}_k) = \emptyset$
- SHA-256 Text Collision between Train and Validation $= 0$.
- Validation partitions evaluate exclusively on original ground-truth transcripts.
