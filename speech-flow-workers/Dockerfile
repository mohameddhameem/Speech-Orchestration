# Workers Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc git

# Install PyTorch (CPU version for LID/Azure, GPU version for Whisper)
# For simplicity, we use a base that supports both, or you can split Dockerfiles.
# Here we assume a GPU-capable base for Whisper, or standard for others.
# For production, create separate Dockerfiles for GPU vs CPU workers.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker sources
COPY . .

# Default command (overridden by k8s)
CMD ["python", "lid/worker.py"]
