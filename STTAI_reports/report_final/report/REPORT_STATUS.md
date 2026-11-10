# REPORT_STATUS.md  -- what is evidenced, and what you must still do

Red **[TBD: ...]** boxes in the PDFs mark evidence that does not exist yet. Search both .tex files for `\TBD{`
(and numbers.tex) -- zero TBDs left = ready. Do NOT fill a TBD with a guessed number.

## Must-fix before Assignment 1 submission
1. Transcripts: final Label Studio exports hold language + intent only. The 182 transcripts come from
   `model/src/asr/curate_gold_transcripts.py` (hand-written mapping). Document who wrote each one, from which clip,
   and have a 2nd person independently transcribe >=100 clips -> report WER between annotators (brief requires it).
   If any of that mapping was AI-written, list the prompt in code/prompts/.
2. Folds are clip-grouped (`GRP_<speaker>_<clip>`), not speaker-grouped; `independent_test_set.json` is EMPTY
   although unseen_speaker_benchmark.json reports 36 samples; fold files say 692/191 samples, leakage report 246/60. Reconcile.
3. Regenerate metadata.csv (SHA-256, timestamp, collector, tool version) for the 182 final clips; re-run the 14-check
   validation suite on them (+ before/after + corruption); add an audio<->text alignment check.
4. DVC-add final_annotation/ and model/data/, push, re-tag. Pin the sentence-transformers model revision.
5. Remove emails/passwords from final_annotation/README.md and any real names from exports (anonymisation requirement).
6. Guideline revision: the brief needs agreement BEFORE and AFTER a revision. Final corpus has one round (kappa 0.656).
   Re-label the 47 disputed clips under a revised guideline (student_services boundary) and report the new kappa.
7. LABELLING_PROTOCOL.md describes the PILOT (transcript-first, lead times "log-normally distributed", seed 7). Rewrite it
   for the final workflow (languages + intent, two instances, expert A3, hidden repeats, dates from the Label Studio DBs).
   The pilot round-1/2 exports/lead-times look script-generated; do not submit them as human annotation unless you can vouch for them.
8. Fill roll numbers, member contributions, AI-assistant names, screenshots (report/shots/*.png).

## Must-fix before Assignment 2 submission
1. Docker: build + run on linux/amd64; `docker run --network none <img> validate`; paste real output; image size, SHA-256,
   container p50/p95/RAM. offline_validation_output.json currently says Darwin + offline_network_isolated:false (LOG-016 'OFFLINE_VERIFIED' not backed).
2. traffic_replay.py: remove `(b_id >= 5)` from the alert rule; replace false-alarm constant by measured many-seed replay.
3. Gate: freeze gate.yaml in a commit BEFORE running; decide on a paired interval not one clip; explain LOG-418 vs LOG-179.
4. Log C-01..C-12 ablation runs in MLflow (add run IDs). Bundle MiniLM weights (no runtime download).
5. Integrate/serve Track-A classifier or state clearly it is offline analysis; run end-to-end ASR->intent on the 182 clips.
6. Fine-tune Whisper decoder properly (hundreds of steps) and serve it, otherwise keep reporting 'no improvement over baseline'.
7. MODEL_CARD.md slices and README claims must match supporting_files/*.json (README still mentions r=0.91 etc. in older versions).

## How numbers flow
numbers.tex (hand-copied from JSON, cited in Evidence Index) + tab_*.tex (auto) + fig_*.pdf (code/scripts/*.py).
