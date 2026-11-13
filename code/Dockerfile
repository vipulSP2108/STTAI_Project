# syntax=docker/dockerfile:1.7
# Voice Helpdesk ASR — indic-v2 CPU image (linux/amd64, offline at run time)
#
# Stage 1 downloads pinned model revisions and converts the two Indic Whisper checkpoints to
# CTranslate2 int8. Stage 2 is the runtime: no model download is possible after the build
# (HF_HUB_OFFLINE=1) and every model is loaded from /opt/models.

FROM python:3.10-slim@sha256:6ff506466f8b1e981719b468cc0023b8ef000b983cdec0eafe119d01f379e31d AS models
RUN python -m pip install --no-cache-dir pip==24.3.1 \
 && python -m pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.5.1+cpu transformers==4.46.3 ctranslate2==4.8.1 huggingface_hub==0.35.3 sentencepiece==0.2.0
ARG BASE_REV=ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66
ARG HINDI_REV=fb4a24afc20c42906deed31c3689e4be31da41fe
ARG GUJARATI_REV=59c972a6f00f529efc7c9b631dff338157561ed9
ARG MINILM_REV=e8f8c211226b894fcb81acc59f3b34ba3efd5f42
RUN HF_HUB_DISABLE_XET=1 python - <<EOF && rm -rf /root/.cache
from huggingface_hub import snapshot_download
from ctranslate2.converters import TransformersConverter
from transformers import WhisperTokenizerFast
import shutil
snapshot_download("Systran/faster-whisper-base", revision="${BASE_REV}", local_dir="/opt/models/whisper-base",
                  allow_patterns=["config.json", "model.bin", "tokenizer.json", "vocabulary.txt"])
snapshot_download("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", revision="${MINILM_REV}",
                  local_dir="/opt/models/minilm",
                  allow_patterns=["*.json", "model.safetensors", "1_Pooling/*", "sentencepiece.bpe.model", "unigram.json"])
for name, repo, rev in [("whisper-hindi-ct2", "vasista22/whisper-hindi-small", "${HINDI_REV}"),
                        ("whisper-gujarati-ct2", "vasista22/whisper-gujarati-base", "${GUJARATI_REV}")]:
    src = snapshot_download(repo, revision=rev, local_dir=f"/tmp/{name}")
    TransformersConverter(src).convert(f"/opt/models/{name}", quantization="int8", force=True)
    WhisperTokenizerFast.from_pretrained(src).backend_tokenizer.save(f"/opt/models/{name}/tokenizer.json")
    shutil.rmtree(src)  # keep only the converted int8 model in this layer
EOF

FROM python:3.10-slim@sha256:6ff506466f8b1e981719b468cc0023b8ef000b983cdec0eafe119d01f379e31d AS runtime
WORKDIR /app
RUN python -m pip install --no-cache-dir pip==24.3.1 \
 && python -m pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu torch==2.5.1+cpu \
    faster-whisper==1.2.1 ctranslate2==4.8.1 sentence-transformers==3.3.1 transformers==4.46.3 \
    fastapi==0.124.0 httpx==0.28.1 jiwer==4.0.0 python-multipart==0.0.20 \
    scikit-learn==1.6.1 scipy==1.14.1 streamlit==1.49.1 uvicorn==0.38.0
COPY --from=models /opt/models /opt/models
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MODEL_DIR=/opt/models PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY code/a2_part_d_deployment/revised_*.py code/a2_part_d_deployment/router_v2.py \
     code/a2_part_d_deployment/revised-entrypoint.sh /app/code/a2_part_d_deployment/
COPY final_annotation/consensus_gold_182.json /app/final_annotation/
COPY model/data/metadata/metadata_182.csv /app/model/data/metadata/
COPY model/data/splits/release_speakers.json /app/model/data/splits/
COPY model/data/reports/offline_asr_predictions.json model/data/reports/lid_features.json /app/model/data/reports/
COPY data/labels/ /app/data/labels/
# Routers are trained here, inside the image, on training/validation speakers only (no test clip).
RUN cd /app/code/a2_part_d_deployment && python revised_release.py train-router

ARG GIT_COMMIT=unknown
ARG SOURCE_TREE=unspecified
ENV GIT_COMMIT=${GIT_COMMIT} SOURCE_TREE=${SOURCE_TREE}
EXPOSE 8000 8501
ENTRYPOINT ["/bin/bash", "/app/code/a2_part_d_deployment/revised-entrypoint.sh"]

FROM runtime AS release
COPY --from=revised_audio / /app/revised_audio/
RUN cd /app/code/a2_part_d_deployment && python revised_release.py check-audio
