FROM python:3.10-slim@sha256:6ff506466f8b1e981719b468cc0023b8ef000b983cdec0eafe119d01f379e31d AS runtime

WORKDIR /app

RUN python -m pip install --no-cache-dir faster-whisper==1.2.1
ARG WHISPER_REVISION=ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66
RUN HF_HUB_DISABLE_XET=1 python -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-base', revision='${WHISPER_REVISION}', local_dir='/opt/whisper-base', allow_patterns=['config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt'])"
RUN python -m pip install --no-cache-dir \
    fastapi==0.124.0 httpx==0.28.1 jiwer==4.0.0 python-multipart==0.0.20 \
    scikit-learn==1.6.1 streamlit==1.49.1 uvicorn==0.38.0

ENV HF_HUB_OFFLINE=1 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY code/a2_part_d_deployment/revised_*.py code/a2_part_d_deployment/revised-entrypoint.sh /app/code/a2_part_d_deployment/
COPY final_annotation/consensus_gold_182.json /app/final_annotation/
COPY model/data/metadata/metadata_182.csv model/data/metadata/gold_transcripts_manifest.json /app/model/data/metadata/
COPY model/data/splits/release_speakers.json /app/model/data/splits/
RUN python code/a2_part_d_deployment/revised_release.py train-router

ARG GIT_COMMIT=unknown
ARG SOURCE_TREE=unspecified
ENV GIT_COMMIT=${GIT_COMMIT} SOURCE_TREE=${SOURCE_TREE}
EXPOSE 8000 8501
ENTRYPOINT ["/bin/bash", "/app/code/a2_part_d_deployment/revised-entrypoint.sh"]

FROM runtime AS release
COPY --from=revised_audio / /app/revised_audio/
RUN python code/a2_part_d_deployment/revised_release.py check-audio
