# Local Development Guide

Run the Speech Orchestration system locally without Azure dependencies.

## Quick Start

```bash
# 1. Start services
docker-compose -f docker-compose.yaml -f docker-compose.local.yml up -d

# 2. Access endpoints
# API: http://localhost:8000/docs
# Dashboard: http://localhost:8501
# RabbitMQ UI: http://localhost:15672 (guest/guest)
```

## What Runs Locally

- **RabbitMQ** - Message queue (replaces Azure Service Bus)
- **Local filesystem** - Storage at `/tmp/speech-flow-storage` (replaces Azure Blob)
- **HuggingFace models** - AI processing (replaces Azure OpenAI)
- **PostgreSQL** - Job database
- **Azurite** - Optional local blob storage emulator

## Configuration

Create `.env` from `.env.local.example`:

```bash
cp .env.local.example .env
```

Key settings:

```bash
ENVIRONMENT=LOCAL
RABBITMQ_URL=******localhost:5672/
LOCAL_STORAGE_PATH=/tmp/speech-flow-storage
DATABASE_URL=******localhost:5432/speechflow
```

## Workers

Start workers individually as needed:

```bash
# Language identification
docker-compose -f docker-compose.yaml -f docker-compose.local.yml up -d worker-lid

# Add more workers
docker-compose -f docker-compose.yaml -f docker-compose.local.yml up -d worker-whisper
```

## Models

HuggingFace models download automatically on first use (~2GB total):

- **Summarization**: facebook/bart-large-cnn
- **Translation**: Helsinki-NLP/opus-mt-{src}-{tgt}

Cached in Docker volume for reuse.

## Testing

```bash
# Submit a job
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"audio_filename": "test.wav", "workflow_type": "full_pipeline"}'

# Check logs
docker-compose logs -f api router worker-lid
```

## Switching to Azure

Set `ENVIRONMENT=AZURE` in `.env` and configure Azure credentials. See main README for details.
