# Local Development Guide

This guide explains how to run the Speech Orchestration system locally without any Azure dependencies.

## Overview

The system supports two modes:
- **AZURE**: Uses Azure Service Bus, Azure Blob Storage, and Azure OpenAI
- **LOCAL**: Uses RabbitMQ, local filesystem storage, and HuggingFace models

## Prerequisites

- Docker and Docker Compose
- At least 8GB RAM (16GB recommended for running all workers)
- 10GB free disk space for models

## Quick Start

### 1. Set Environment to LOCAL

Create a `.env` file in the root directory:

```bash
cp .env.local.example .env
```

Edit `.env` and ensure `ENVIRONMENT=LOCAL` is set:

```
ENVIRONMENT=LOCAL
```

### 2. Start Services

Start the infrastructure and backend services:

```bash
docker-compose up -d postgres rabbitmq azurite api router dashboard
```

This will start:
- PostgreSQL database
- RabbitMQ message broker (with management UI at http://localhost:15672)
- Azurite local blob storage
- API server (http://localhost:8000)
- Router service
- Dashboard (http://localhost:8501)

### 3. Start Workers (Optional)

Workers can be started individually based on your needs:

```bash
# Language Identification worker
docker-compose up -d worker-lid

# Add more workers as needed
```

### 4. Verify Services

Check that all services are running:

```bash
docker-compose ps
```

Access the services:
- API: http://localhost:8000/docs (Swagger UI)
- Dashboard: http://localhost:8501
- RabbitMQ Management: http://localhost:15672 (username: guest, password: guest)

## Architecture Differences

### LOCAL Mode

When `ENVIRONMENT=LOCAL`:

1. **Message Queue**: RabbitMQ instead of Azure Service Bus
   - Connection: `amqp://guest:guest@localhost:5672/`
   - Management UI: http://localhost:15672

2. **Storage**: Local filesystem instead of Azure Blob Storage
   - Default path: `/tmp/speech-flow-storage`
   - Configurable via `LOCAL_STORAGE_PATH` environment variable

3. **AI Models**: HuggingFace models instead of Azure OpenAI
   - Summarization: `facebook/bart-large-cnn` (configurable via `HF_SUMMARIZATION_MODEL`)
   - Translation: `Helsinki-NLP/opus-mt-{src}-{tgt}` (configurable via `HF_TRANSLATION_MODEL`)
   - **Note**: Models are downloaded on first use and cached locally
   - **Cost**: Free (unlike Azure OpenAI which has per-token costs)

### AZURE Mode

When `ENVIRONMENT=AZURE`:

1. **Message Queue**: Azure Service Bus
2. **Storage**: Azure Blob Storage
3. **AI Models**: Azure OpenAI

## Configuration

### Environment Variables

Key environment variables for local mode:

```bash
# Required
ENVIRONMENT=LOCAL

# RabbitMQ (default values shown)
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Local Storage
LOCAL_STORAGE_PATH=/tmp/speech-flow-storage

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/speechflow

# HuggingFace Models
HF_SUMMARIZATION_MODEL=facebook/bart-large-cnn
HF_TRANSLATION_MODEL=Helsinki-NLP/opus-mt-{src}-{tgt}
```

### Switching Between Modes

To switch between LOCAL and AZURE modes:

1. Update the `ENVIRONMENT` variable in your `.env` file
2. Restart the services:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Testing the System

### Submit a Test Job

```bash
# Submit a job
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "audio_filename": "test.wav",
    "workflow_type": "full_pipeline"
  }'

# Get job status
curl http://localhost:8000/jobs/{job_id}

# Get results
curl http://localhost:8000/jobs/{job_id}/results
```

### View Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f router
docker-compose logs -f worker-lid
```

## Model Download and Caching

When using LOCAL mode with HuggingFace models:

1. Models are downloaded from HuggingFace Hub on first use
2. Models are cached in the `model_cache` Docker volume
3. Subsequent runs will use the cached models

To pre-download models, you can run:

```bash
# Start a worker to trigger model download
docker-compose up worker-lid

# The worker will download and cache the required models
# You can then stop it with Ctrl+C
```

## Troubleshooting

### RabbitMQ Connection Issues

Check if RabbitMQ is running:
```bash
docker-compose ps rabbitmq
docker-compose logs rabbitmq
```

### Model Download Issues

If HuggingFace model downloads fail:
1. Check your internet connection
2. Increase Docker memory limits (models can be large)
3. Check available disk space

### Storage Issues

Local storage is in `/tmp/speech-flow-storage` by default. To use a different location:
```bash
LOCAL_STORAGE_PATH=/path/to/storage docker-compose up
```

## Performance Considerations

### Local Mode

- **Pros**:
  - No cloud costs
  - Works offline (after initial model download)
  - Easier to debug and develop
  - Full data privacy

- **Cons**:
  - Slower AI inference (CPU vs GPU)
  - Lower quality translations/summaries compared to GPT-4
  - Requires more local resources

### Azure Mode

- **Pros**:
  - Better AI quality (GPT-4)
  - Scalable infrastructure
  - Managed services

- **Cons**:
  - Costs per API call
  - Requires internet connection
  - Data leaves your system

## Development Workflow

1. Set `ENVIRONMENT=LOCAL`
2. Start services with `docker-compose up`
3. Make code changes
4. Services auto-reload (backend has `--reload` flag)
5. Test changes locally
6. Switch to `ENVIRONMENT=AZURE` for production deployment

## Additional Resources

- RabbitMQ Documentation: https://www.rabbitmq.com/documentation.html
- HuggingFace Transformers: https://huggingface.co/docs/transformers
- Pika (RabbitMQ Python client): https://pika.readthedocs.io/

## Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Verify environment variables: `docker-compose config`
3. Check service health: `docker-compose ps`
