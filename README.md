# Speech Orchestration Pipeline

Event-driven speech processing system supporting both local development and Azure cloud deployment.

## Quick Start

### Local Development (No Azure Required)

```bash
# Start all services locally
docker-compose -f docker-compose.yaml -f docker-compose.local.yml up -d

# Access services
# API: http://localhost:8000/docs
# Upload UI: http://localhost:8502 (Simple audio upload and results download)
# Operations Dashboard: http://localhost:8501 (Monitoring and analytics)
# RabbitMQ: http://localhost:15672 (guest/guest)
```

### Azure Production

```bash
# Set environment
export ENVIRONMENT=AZURE
export AZURE_STORAGE_ACCOUNT_URL=https://mystorageaccount.blob.core.windows.net
export SERVICEBUS_FQDN=myservicebus.servicebus.windows.net
export AZURE_OPENAI_ENDPOINT=https://myopenai.openai.azure.com/
export AZURE_OPENAI_DEPLOYMENT=gpt-4

# Start services
docker-compose up -d
```

## Architecture

### Local Mode (`ENVIRONMENT=LOCAL`)
- **Message Queue**: RabbitMQ
- **Storage**: Local filesystem (`/tmp/speech-flow-storage`)
- **AI Models**: HuggingFace (BART for summarization, OPUS-MT for translation)
- **Cost**: Free
- **Internet**: Optional (after initial model download)

### Azure Mode (`ENVIRONMENT=AZURE`)
- **Message Queue**: Azure Service Bus
- **Storage**: Azure Blob Storage
- **AI Models**: Azure OpenAI (GPT-4)
- **Authentication**: DefaultAzureCredential (supports Managed Identity, Client Secret, Azure CLI)

## Configuration

### Environment Variables

```bash
# Mode selector
ENVIRONMENT=LOCAL  # or AZURE

# Local mode settings
RABBITMQ_URL=******localhost:5672/
LOCAL_STORAGE_PATH=/tmp/speech-flow-storage
HF_SUMMARIZATION_MODEL=facebook/bart-large-cnn
HF_TRANSLATION_MODEL=Helsinki-NLP/opus-mt-{src}-{tgt}

# Azure mode settings (DefaultAzureCredential)
AZURE_STORAGE_ACCOUNT_URL=https://account.blob.core.windows.net
SERVICEBUS_FQDN=namespace.servicebus.windows.net
AZURE_OPENAI_ENDPOINT=https://resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Common settings
DATABASE_URL=******localhost:5432/speechflow
ROUTER_QUEUE_NAME=job-events
LID_QUEUE_NAME=lid-jobs
WHISPER_QUEUE_NAME=whisper-jobs
AZURE_AI_QUEUE_NAME=azure-ai-jobs
```

### Azure Authentication

DefaultAzureCredential automatically tries authentication methods in this order:

1. **Environment Variables** (Client Secret)
   ```bash
   AZURE_CLIENT_ID=...
   AZURE_CLIENT_SECRET=...
   AZURE_TENANT_ID=...
   ```

2. **Managed Identity** (recommended for production)
   - System-Assigned Managed Identity (SAMI)
   - User-Assigned Managed Identity (UAMI)

3. **Azure CLI** (for local development)

4. **Interactive browser**

## Project Structure

```
speech-flow-backend/
  ├── api/              # REST API endpoints
  ├── router/           # Job orchestration
  ├── dashboard/        # Operations monitoring dashboard
  ├── config.py         # Configuration
  ├── messaging_adapter.py   # Message queue abstraction
  ├── storage_adapter.py     # Storage abstraction
  └── requirements.txt

speech-flow-ui/
  ├── app.py            # Self-service upload UI
  ├── requirements.txt  # UI dependencies
  ├── Dockerfile       # Container image
  └── README.md

speech-flow-workers/
  ├── common/
  │   ├── base_worker.py     # Base worker class
  │   ├── ai_adapter.py      # AI model abstraction
  │   └── model_manager.py   # Model caching
  ├── lid/              # Language identification
  ├── whisper/          # Speech transcription
  └── azure_ai/         # Translation & summarization
```

## Development

### Prerequisites
- Docker & Docker Compose
- 8GB RAM (16GB recommended for workers)
- 10GB disk space (for AI models)

### Testing

```bash
# Start infrastructure
docker-compose -f docker-compose.yaml -f docker-compose.local.yml up -d postgres rabbitmq azurite

# Start API
docker-compose -f docker-compose.yaml -f docker-compose.local.yml up -d api router dashboard

# Submit a job
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"audio_filename": "test.wav", "workflow_type": "full_pipeline"}'

# Check status
curl http://localhost:8000/jobs/{job_id}
```

## Models (Local Mode)

Models are auto-downloaded on first use and cached in Docker volume:

- **Summarization**: facebook/bart-large-cnn (~1.6GB, 2-5s per summary on CPU)
- **Translation**: Helsinki-NLP/opus-mt language pairs (~300MB each, 1-3s per translation on CPU)

## Deployment

### Local Development
```bash
cp .env.local.example .env
# Edit .env to customize settings
docker-compose -f docker-compose.yaml -f docker-compose.local.yml up -d
```

### Azure (Managed Identity)
```bash
# Configure environment variables
export ENVIRONMENT=AZURE
export AZURE_STORAGE_ACCOUNT_URL=...
export SERVICEBUS_FQDN=...
export AZURE_OPENAI_ENDPOINT=...

# Deploy with Managed Identity (no secrets needed)
docker-compose up -d
```

### Azure (Client Secret)
```bash
export ENVIRONMENT=AZURE
export AZURE_CLIENT_ID=...
export AZURE_CLIENT_SECRET=...
export AZURE_TENANT_ID=...
export AZURE_STORAGE_ACCOUNT_URL=...
export SERVICEBUS_FQDN=...
export AZURE_OPENAI_ENDPOINT=...

docker-compose up -d
```

## Services

- **API** (port 8000): Job submission and status
- **Upload UI** (port 8502): Simple web interface for audio upload and results download
- **Operations Dashboard** (port 8501): Monitoring and metrics
- **Router**: Job orchestration and workflow management
- **Workers**: LID, Whisper transcription, Azure AI translation/summarization
- **PostgreSQL** (port 5432): Job metadata
- **RabbitMQ** (port 5672, 15672): Local message queue
- **Azurite** (port 10000): Local blob storage emulator

## Troubleshooting

**RabbitMQ connection issues:**
```bash
docker-compose logs rabbitmq
docker-compose ps rabbitmq
```

**Model download failures:**
- Check internet connection
- Increase Docker memory limit
- Verify disk space

**Azure authentication issues:**
```bash
# Test Azure CLI login
az login
az account show

# Test Managed Identity (on Azure VM/Container)
curl -H Metadata:true "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://storage.azure.com/"
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
