#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""cli.py - Unified Command-Line Interface for the Multilingual Model Pipeline.

IIT Gandhinagar - CS203 / Project 5 (Voice Helpdesk Multilingual System)

Commands:
  audit         Audit dataset health and class distribution
  transcribe    Execute offline multilingual speech recognition
  curate        Curate authentic native-script ground-truth transcripts
  evaluate-asr  Compute WER, CER, Character accuracy, and lexical match
  sanitize      Strip non-linguistic metadata and package into UUIDs
  augment       Run multilingual augmentation with semantic quality gates
  split         Perform leakage-free StratifiedGroupKFold partitioning
  verify        Audit cross-fold isolation and verify zero data leakage
  ablate        Execute mandatory 10-configuration augmentation ablation study
  benchmark     Run generalization evaluation on unseen speakers and language slices
"""

import os
import sys
import argparse
from pathlib import Path

# Guarantee python environment
os.environ["PATH"] = f"/Library/Frameworks/Python.framework/Versions/3.13/bin:/opt/homebrew/bin:{os.environ.get('PATH', '')}"

def main():
    parser = argparse.ArgumentParser(
        prog="python -m model.cli",
        description="Unified CLI for IITGN Multilingual Voice Helpdesk Model Pipeline"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. Audit
    p_audit = subparsers.add_parser("audit", help="Audit dataset health and class distribution")

    # 2. Transcribe
    p_transcribe = subparsers.add_parser("transcribe", help="Run offline multilingual ASR")
    p_transcribe.add_argument("--max", type=int, default=None, help="Max clips to transcribe")

    # 3. Curate
    p_curate = subparsers.add_parser("curate", help="Curate authentic native-script gold transcripts")

    # 4. Evaluate ASR
    p_ev_asr = subparsers.add_parser("evaluate-asr", help="Evaluate offline ASR against gold ground truth")

    # 5. Sanitize
    p_sanitize = subparsers.add_parser("sanitize", help="Strip metadata and package audio/text UUIDs")

    # 6. Augment
    p_augment = subparsers.add_parser("augment", help="Run multilingual augmentation with quality gates")
    p_augment.add_argument("--threshold", type=float, default=0.82, help="Cosine similarity threshold")

    # 7. Split
    p_split = subparsers.add_parser("split", help="Generate StratifiedGroupKFold splits")
    p_split.add_argument("--folds", type=int, default=5, help="Number of folds (default: 5)")

    # 8. Verify Leakage
    p_verify = subparsers.add_parser("verify", help="Audit cross-fold isolation and verify zero leakage")

    # 9. Ablate
    p_ablate = subparsers.add_parser("ablate", help="Run 10-configuration augmentation ablation study")

    # 10. Benchmark
    p_bench = subparsers.add_parser("benchmark", help="Run unseen speaker & language slice benchmark")

    args = parser.parse_args()

    if args.command == "audit":
        from model.src.sanitization.uuid_packager import generate_dataset_summary
        generate_dataset_summary()

    elif args.command == "transcribe":
        from model.src.asr.transcribe import run_transcription
        run_transcription(max_clips=args.max)

    elif args.command == "curate":
        from model.src.asr.curate_gold_transcripts import clean_and_curate
        clean_and_curate()

    elif args.command == "evaluate-asr":
        from model.src.asr.evaluate_asr import evaluate_asr_engine
        evaluate_asr_engine()

    elif args.command == "sanitize":
        from model.src.sanitization.uuid_packager import package_dataset
        package_dataset()

    elif args.command == "augment":
        from model.src.augmentation.pipeline import run_augmentation_pipeline
        run_augmentation_pipeline(similarity_threshold=args.threshold)

    elif args.command == "split":
        from model.src.splitting.group_splitter import create_splits
        create_splits(n_splits=args.folds)

    elif args.command == "verify":
        from model.src.splitting.leakage_auditor import verify_all_splits
        verify_all_splits()

    elif args.command == "ablate":
        from model.src.training.ablation_runner import run_ablation_study
        run_ablation_study()

    elif args.command == "benchmark":
        from model.src.evaluation.unseen_speaker_test import run_unseen_speaker_benchmark
        run_unseen_speaker_benchmark()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
