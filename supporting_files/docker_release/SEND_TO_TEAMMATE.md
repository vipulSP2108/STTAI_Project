# Docker archive handoff — 12 November 2026

Built unchanged from commit `0ec5ed1dca5b4e56dcde2585fdc9c95c43d57481` using a clean Git snapshot. No model code was edited to make the build or validation pass. Audio stayed outside the Git checkout.

## Files to share

1. `docker_image.tar.gz` — 1,466,489,118 bytes (about 1.47 GB). Upload this file to Drive and supply the download link; no upload/public sharing has been performed here.
2. SHA-256: `4d174accc18db803e982ae05919d215792cb34d8905ef971ae08136ee1067ad4` (also in `docker_image.tar.gz.sha256`).
3. Image ID: `sha256:362a326553d6d84c5592b435874f652aec0a70bbb17866a12ede61e0bebae972`.
4. Full evaluation JSON: `offline_validation.json`; terminal output: `offline_validation.log`.
5. OS/CPU/RAM and Docker details: `environment.json` and `docker_version.txt`.

## Result

- Image tag: `voice-helpdesk-asr:indic-v2`, linux/amd64.
- Build: exit 0; trained routers inside Docker on 104 train + 38 validation clips; 44 bundled audio hash/format/duration checks passed.
- Offline validation: exit 0, 40 test clips, `--network none`, no host file mounts. See `offline_container_proof.json`.
- Intent accuracy: 60.0%; macro F1: 0.594805.
- Language-route accuracy: 72.5%. This is the measured result, slightly below the note's approximate 75% expectation.
- WER/CER: unavailable; zero human transcript references bundled. Round T must finish before transcript-based evaluation can be reported.
- Latency p50: 7.10 s; p95: 26.05 s; CPU real-time factor: 0.3456; peak process RSS: 1712.42 MiB. Measurements were taken while archive packaging/reload also ran, so timings reflect concurrent machine activity.
- Gzip CRC and Docker archive manifest/tag checks passed. Docker successfully loaded the gzip archive with the same image ID; see `archive_load_verification.log`.
- Machine: Microsoft Windows 11 Home Single Language (10.0.26300), AMD Ryzen 7 7840HS w/ Radeon 780M Graphics, 15.19 GiB RAM.

The friend's note accepts JSON text OR a screenshot. The actual JSON and log are supplied; no screenshot is claimed. This does not replace any separate assignment screenshot requirement.

## Use the archive

```powershell
docker load -i docker_image.tar.gz
docker run --rm --network none voice-helpdesk-asr:indic-v2 validate
# For the interactive app (after stopping any other service on these ports):
docker run --rm -p 8000:8000 -p 8501:8501 voice-helpdesk-asr:indic-v2
```

The archive contains the runtime, model weights, trained routers, and release WAVs. It does not depend on the host Python environment or host model/audio mounts.

## Evaluation terminal JSON

```json
{
  "model_version": "indic-v2-lid-router-b3-expert",
  "asr_revision": "ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66",
  "revisions": {
    "faster-whisper-base": "Systran/faster-whisper-base@ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66",
    "whisper-hindi-small": "vasista22/whisper-hindi-small@fb4a24afc20c42906deed31c3689e4be31da41fe",
    "whisper-gujarati-base": "vasista22/whisper-gujarati-base@59c972a6f00f529efc7c9b631dff338157561ed9",
    "minilm": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2@e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
  },
  "git_commit": "0ec5ed1dca5b4e56dcde2585fdc9c95c43d57481",
  "source_tree": "clean",
  "split": "revised_release_test",
  "speaker_split_sha256": "982ecebfb76496c4c32d1164dc6d0d41de0d435ef077a24cab2ed68ecbbd92a5",
  "sample_count": 40,
  "intent_accuracy": 0.6,
  "intent_macro_f1": 0.5948051948051948,
  "language_route_accuracy": 0.725,
  "wer": null,
  "cer": null,
  "wer_reference_count": 0,
  "wer_status": "not computed: no human transcripts bundled (curated text withdrawn)",
  "cpu_latency_ms_p50": 7096.355,
  "cpu_latency_ms_p95": 26053.175499999998,
  "cpu_rtf": 0.3456407859115544,
  "peak_rss_mib": 1712.42
}
```

## Still to do

- User uploads the archive and shares the Drive link with the teammate.
- A2 finishes the 141-task transcription assignment at http://localhost:8092, exports A2.json, and stops the Label Studio container when done. The 100 shared items are independently transcribed without ASR drafts; the 41 single items have drafts to correct.
- Team merges/adjudicates Round T transcripts, evaluates transcript agreement/WER, and rebuilds a later archive if release inputs change. This archive records today's committed model, not future transcript work.
