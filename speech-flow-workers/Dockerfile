# Workers Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc git && \
    rm -rf /var/lib/apt/lists/*

# Install PyTorch (CPU version for LID/Azure, GPU version for Whisper)
# For simplicity, we use a base that supports both, or you can split Dockerfiles.
# Here we assume a GPU-capable base for Whisper, or standard for others.
# For production, create separate Dockerfiles for GPU vs CPU workers.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker sources
COPY . .

# Set default model cache directory (can be overridden by volume mount)
ENV MODEL_CACHE_DIR=/models
RUN mkdir -p /models

# Optional: Pre-download models at build time (commented out by default)
# Uncomment to pre-download models during image build (increases image size but faster startup)
# ARG PRELOAD_MODELS=false
# RUN if [ "$PRELOAD_MODELS" = "true" ]; then \
#     python -c "from common.model_manager import get_model_manager; \
#                mm = get_model_manager(); \
#                mm.load_whisper_model(); \
#                mm.load_lid_model()"; \
#     fi

# Default command (overridden by k8s)
CMD ["python", "lid/worker.py"]
