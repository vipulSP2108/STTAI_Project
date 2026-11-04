# ============================================================
# Assignment 2 - Part D: Production Dockerfile (Self-Contained CPU Image)
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR
#
# Pinned Base Image: python:3.10-slim
# Target Platform: linux/amd64 (CPU Only execution)
# Peak RAM Requirement: <= 4.2 GB RAM (Brief limit: <= 16 GB RAM)
#
# Usage:
#   1. Offline Gold Set Validation (strict --network none):
#      docker run --rm --network none voice-helpdesk-asr:a2-final validate
#   2. Start Web Service and UI:
#      docker run --rm -p 8501:8501 -p 8000:8000 voice-helpdesk-asr:a2-final
# ============================================================

FROM python:3.10-slim

# Install system audio and compilation tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GIT_COMMIT=a2-final \
    MODEL_VERSION=production \
    PORT=8501

# Copy pinned requirements and install
COPY code/requirements.txt /app/code/requirements.txt
RUN pip install --no-cache-dir -r /app/code/requirements.txt

# Pre-cache Whisper base model weights for true offline operation (--network none)
RUN python3 -c "import whisper; whisper.load_model('base')"

# Copy source repository artifacts
COPY code/ /app/code/
COPY data/ /app/data/
COPY supporting_files/ /app/supporting_files/
COPY artefacts/ /app/artefacts/
COPY TEST_SET_LOG.md /app/TEST_SET_LOG.md

# Verification assert on build
RUN python3 -c "import hashlib; h = hashlib.sha256(open('data/gold_test_set.csv', 'rb').read()).hexdigest(); assert h == '64b7647b5d0d35733063c77caab122a1a7c24ac6c70b7d476ffbabd9a2448ca9', 'Build failed: gold hash altered!'"

EXPOSE 8501 8000

# Entrypoint script
RUN echo '#!/bin/bash\n\
if [ "$1" = "validate" ]; then\n\
    exec python3 code/a2_part_d_deployment/validate_offline.py\n\
else\n\
    python3 code/a2_part_d_deployment/app.py &\n\
    exec streamlit run code/a2_part_d_deployment/ui.py --server.port=8501 --server.address=0.0.0.0\n\
fi' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
