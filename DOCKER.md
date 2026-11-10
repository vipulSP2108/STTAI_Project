# Revised Voice Helpdesk Docker image

The revised CPU image serves Faster Whisper base INT8 and a character TF-IDF intent router. The image build trains the router on 104 revised training references and their adjudicated labels. It packages the public ASR weights at build time. The release bundles 40 test WAVs and four validation examples from a separate DVC staging folder. The runtime target used in CI excludes the corpus WAVs.

The revised speaker split is `model/data/splits/release_speakers.json`. Training, validation, and test have disjoint speaker IDs. The revised validator measures all 40 clips from that split against the curated references. It is separate from the original A1 frozen gold benchmark, which remains in `data/gold_test_set.csv`. The revised run measures a baseline on this release split. It does not establish that its speakers were unseen by historical experiments or satisfy the course's acoustic fine-tuning requirement.

## Build locally

Use a disposable checkout for the DVC restore. The local Windows store is documented in `ASSIGNMENT_CHECKPOINT_PLAN.md`. In this example the verified full WAV folder is `$env:USERPROFILE\Downloads\STTAI_Project_Docker_Stage\model\data\audio`. Substitute the path from your disposable checkout when using the team remote.

Run from the project root in PowerShell.

```powershell
$wavDir = Join-Path $env:USERPROFILE 'Downloads\STTAI_Project_Docker_Stage\model\data\audio'
$bundle = Join-Path $env:USERPROFILE 'Downloads\STTAI_Project_Release_Audio'
# Stage once into a new directory. The image build also verifies the bundled WAVs.
if (-not (Test-Path -LiteralPath $bundle)) {
    python code/a2_part_d_deployment/revised_data.py $wavDir $bundle
    if ($LASTEXITCODE -ne 0) { throw 'Audio staging failed' }
}
$commit = git rev-parse HEAD
docker build --platform linux/amd64 --target release `
  --build-context "revised_audio=$bundle" `
  --build-arg "GIT_COMMIT=$commit" --build-arg SOURCE_TREE=working-tree `
  -t voice-helpdesk-asr:revised-release -f code/Dockerfile .
```

Use `SOURCE_TREE=clean` for a clean checkout of the identified commit. The base image is pinned by digest in the Dockerfile. The upstream model is `Systran/faster-whisper-base` at revision `ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66`. Build-time package and model downloads are required. The deployed processes read bundled weights and make local inference calls.

## Offline validation and local UI

```powershell
$evidence = (Resolve-Path supporting_files).Path
docker run --rm --pull never --network none `
  --mount "type=bind,source=$evidence,target=/evidence" `
  voice-helpdesk-asr:revised-release validate --output /evidence/revised_validation.json
docker run --rm --pull never -p 127.0.0.1:8501:8501 `
  --mount "type=bind,source=$evidence,target=/evidence,readonly" `
  voice-helpdesk-asr:revised-release serve
```

Open `http://127.0.0.1:8501`. The UI supports bundled validation examples, WAV upload and microphone input. It shows the returned transcript, intent, confidence, latency and model version. It displays the measured validation JSON when its model and build identity match. Add `-p 127.0.0.1:8000:8000` before the image name to expose the REST API locally. Its endpoints are `GET /health`, `GET /version` and `POST /predict` (multipart field `file`, WAV up to 12 MiB). The API decodes WAV uploads to 16 kHz mono in memory. The benchmark and CI source fixture retain their strict format and integrity checks. CI also tests a 44.1 kHz stereo version of the fixture through `/predict`.

The offline validator checks the WAV hashes and format before decoding and fails if any required WAV is absent or invalid. Its JSON includes the split checksum, counts, WER/CER, intent accuracy/macro-F1, CPU p50/p95, RTF and peak process RSS. The local run on Docker Engine 29.9.3 exited 0 with network mode `none`. The tested image was 1,971,418,582 bytes and the validator peaked at 648.95 MiB process RSS. See [validation JSON](supporting_files/revised_validation.json), [Docker Desktop screenshot](supporting_files/revised_validation.jpg), and [API and UI checks](supporting_files/revised_service_smoke.json). The earlier `docker_asr_smoke.jpg` shows the separate ASR-only image.

## CI and image distribution

The workflow builds `--target runtime` and exercises health/version/prediction with a synthetic WAV and `--network none`. Full release validation requires the privately restored WAVs. Record a remote Actions run after publishing the source changes.

Package a team-approved release image outside Git after confirming permission to distribute its bundled clips. Use `docker save -o revised-release.tar voice-helpdesk-asr:revised-release`, hash the archive, and record its digest with the download location. On the grader machine use `docker load -i revised-release.tar` and repeat the offline validator. Record image size, architecture and the full JSON from that load test separately from this local evidence.
