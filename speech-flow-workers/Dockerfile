# Workers Dockerfile - Multi-stage build with security hardening

# Stage 1: Builder
FROM python:3.10-slim as builder

WORKDIR /build

# Install build dependencies only in builder stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN python -m pip install --upgrade pip setuptools wheel

# Copy requirements first (better layer caching)
COPY speech-flow-workers/requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim

# Install only runtime dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_INPUT=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy worker sources with proper ownership
COPY --chown=appuser:appuser speech-flow-workers/ .

# Switch to non-root user
USER appuser

# Health check (basic process check)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import psutil; psutil.Process(1)" 2>/dev/null || exit 1

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
