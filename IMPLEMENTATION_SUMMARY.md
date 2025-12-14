# Local Development Implementation Summary

## Overview

This implementation adds support for running the Speech Orchestration system completely locally without any Azure dependencies. Users can now test the entire system end-to-end using:
- RabbitMQ instead of Azure Service Bus
- Local filesystem instead of Azure Blob Storage  
- HuggingFace models instead of Azure OpenAI

## Key Changes

### 1. Environment Configuration (`ENVIRONMENT` variable)

Added a new `ENVIRONMENT` variable that controls which services are used:
- `ENVIRONMENT=AZURE` (default): Uses Azure Service Bus, Azure Blob Storage, Azure OpenAI
- `ENVIRONMENT=LOCAL`: Uses RabbitMQ, local filesystem, HuggingFace models

### 2. Adapter Pattern Implementation

Created three adapter modules that provide a unified interface for different backends:

#### **Messaging Adapter** (`speech-flow-backend/messaging_adapter.py`)
- `AzureServiceBusAdapter`: Wraps Azure Service Bus client
- `RabbitMQAdapter`: Wraps Pika (RabbitMQ Python client)
- `get_message_broker()`: Factory function that returns appropriate adapter based on `ENVIRONMENT`

#### **Storage Adapter** (`speech-flow-backend/storage_adapter.py`)
- `AzureBlobStorageAdapter`: Wraps Azure Blob Storage client
- `LocalFileStorageAdapter`: Uses local filesystem
- `get_storage_adapter()`: Factory function that returns appropriate adapter based on `ENVIRONMENT`

#### **AI Adapter** (`speech-flow-workers/common/ai_adapter.py`)
- `AzureOpenAIAdapter`: Wraps Azure OpenAI client
- `HuggingFaceAdapter`: Uses HuggingFace Transformers models
- `get_ai_adapter()`: Factory function that returns appropriate adapter based on `ENVIRONMENT`

### 3. Updated Components

Modified the following files to use adapters instead of direct Azure SDK calls:
- `speech-flow-workers/common/base_worker.py`: Worker base class
- `speech-flow-workers/azure_ai/worker.py`: AI worker for translation/summarization
- `speech-flow-backend/api/main.py`: API endpoints
- `speech-flow-backend/router/main.py`: Job router service
- `speech-flow-backend/config.py`: Configuration settings

### 4. Docker Compose Enhancements

Updated `docker-compose.yaml` to include:
- RabbitMQ service with management UI (port 15672)
- Environment variables for switching modes
- Volume for local storage
- Health checks for all services

### 5. Dependencies

Added to `requirements.txt`:
- `pika==1.3.2`: RabbitMQ client for Python

HuggingFace models are already included in the workers' `transformers` dependency.

### 6. Documentation

Created comprehensive documentation:
- `LOCAL_DEVELOPMENT.md`: Complete guide for local development
- `.env.local.example`: Example environment configuration
- This summary document

## Usage

### Quick Start - Local Mode

1. Create `.env` file:
   ```bash
   cp .env.local.example .env
   ```

2. Set environment to LOCAL:
   ```bash
   ENVIRONMENT=LOCAL
   ```

3. Start services:
   ```bash
   docker-compose up -d postgres rabbitmq azurite api router dashboard
   ```

4. Access services:
   - API: http://localhost:8000/docs
   - Dashboard: http://localhost:8501
   - RabbitMQ Management: http://localhost:15672 (guest/guest)

### Quick Start - Azure Mode

1. Create `.env` file with Azure credentials:
   ```bash
   ENVIRONMENT=AZURE
   AZURE_STORAGE_CONNECTION_STRING=...
   SERVICEBUS_CONNECTION_STRING=...
   AZURE_OPENAI_ENDPOINT=...
   AZURE_OPENAI_KEY=...
   ```

2. Start services:
   ```bash
   docker-compose up -d
   ```

## Architecture Details

### Message Flow - LOCAL Mode

```
API → RabbitMQ → Router → RabbitMQ → Workers
                    ↓
              PostgreSQL
                    ↓
            Local Filesystem
```

### Message Flow - AZURE Mode

```
API → Azure Service Bus → Router → Azure Service Bus → Workers
                              ↓
                        PostgreSQL
                              ↓
                     Azure Blob Storage
```

## Benefits

### Local Mode Benefits
1. **No Cloud Costs**: Free to run completely locally
2. **Offline Development**: Works without internet (after initial model download)
3. **Data Privacy**: All data stays on local machine
4. **Fast Iteration**: Quick startup and testing
5. **Easy Debugging**: All services accessible locally

### Backward Compatibility
- Default mode is still AZURE
- No breaking changes to existing deployments
- All existing Azure features still work
- Easy to switch between modes

## Performance Considerations

### Local Mode
- **Messaging**: RabbitMQ is very fast for local development
- **Storage**: Local filesystem is faster than blob storage
- **AI Models**: Slower than Azure OpenAI (CPU vs cloud GPUs)
  - First run downloads models (~500MB-1GB per model)
  - Subsequent runs use cached models
  - Inference is slower but acceptable for development

### Azure Mode
- **Messaging**: Azure Service Bus handles high throughput
- **Storage**: Azure Blob Storage is scalable and durable
- **AI Models**: Azure OpenAI provides best quality and speed

## Model Information

### HuggingFace Models Used (LOCAL mode)

1. **Summarization**: `facebook/bart-large-cnn`
   - Size: ~1.6GB
   - Quality: Good for general summarization
   - Speed: ~2-5 seconds per summary on CPU

2. **Translation**: `Helsinki-NLP/opus-mt-{src}-{tgt}`
   - Size: ~300MB per language pair
   - Quality: Good for common language pairs
   - Speed: ~1-3 seconds per translation on CPU
   - Fallback: `facebook/nllb-200-distilled-600M` for unsupported pairs

Models are automatically downloaded on first use and cached in the `model_cache` Docker volume.

## Configuration Variables

### Core Settings
- `ENVIRONMENT`: `LOCAL` or `AZURE` (default: `AZURE`)

### Local Mode Settings
- `RABBITMQ_URL`: RabbitMQ connection string (default: `amqp://guest:guest@localhost:5672/`)
- `LOCAL_STORAGE_PATH`: Local storage directory (default: `/tmp/speech-flow-storage`)
- `HF_SUMMARIZATION_MODEL`: HuggingFace summarization model (default: `facebook/bart-large-cnn`)
- `HF_TRANSLATION_MODEL`: HuggingFace translation model template (default: `Helsinki-NLP/opus-mt-{src}-{tgt}`)

### Azure Mode Settings
- `AZURE_STORAGE_CONNECTION_STRING`: Azure Blob Storage connection
- `SERVICEBUS_CONNECTION_STRING`: Azure Service Bus connection
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_OPENAI_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT`: Deployment name (default: `gpt-4`)

### Common Settings
- `DATABASE_URL`: PostgreSQL connection string
- `ROUTER_QUEUE_NAME`, `LID_QUEUE_NAME`, `WHISPER_QUEUE_NAME`, `AZURE_AI_QUEUE_NAME`: Queue names

## Testing

### Manual Testing

1. Start all services in LOCAL mode
2. Submit a job via API:
   ```bash
   curl -X POST http://localhost:8000/jobs \
     -H "Content-Type: application/json" \
     -d '{"audio_filename": "test.wav", "workflow_type": "full_pipeline"}'
   ```
3. Check RabbitMQ management UI to see messages flowing
4. Check local storage directory for uploaded files
5. Monitor logs: `docker-compose logs -f`

### Automated Testing

Run the test script:
```bash
python3 test_local_setup.py
```

This tests:
- Storage adapter creation and basic operations
- AI adapter creation
- Configuration loading

## Troubleshooting

### Common Issues

1. **RabbitMQ connection refused**
   - Ensure RabbitMQ is running: `docker-compose ps rabbitmq`
   - Check logs: `docker-compose logs rabbitmq`

2. **Model download fails**
   - Check internet connection
   - Increase Docker memory limits
   - Check disk space (models can be large)

3. **Storage permission errors**
   - Ensure LOCAL_STORAGE_PATH directory is writable
   - Check Docker volume permissions

4. **Import errors**
   - Ensure pika is installed: `pip install pika==1.3.2`
   - Check Python path includes adapter modules

## Future Enhancements

Potential improvements for local development:

1. **Async RabbitMQ**: Replace blocking pika with aio_pika for better async support
2. **Model Preloading**: Script to pre-download all models
3. **Docker Image**: Pre-built image with models included
4. **Mock Mode**: Even lighter mode with mocked AI responses for UI testing
5. **Performance Metrics**: Compare LOCAL vs AZURE mode performance

## Security Notes

- Default development keys in `config.py` are for local development only
- Never commit real Azure credentials to version control
- Use `.env` file (gitignored) for sensitive configuration
- RabbitMQ default credentials (guest/guest) should be changed for any non-local deployment

## Migration Guide

### From Azure-only to Multi-mode

Existing deployments are not affected. To enable local development:

1. Pull latest code
2. Install new dependency: `pip install pika==1.3.2`
3. Create `.env` with `ENVIRONMENT=LOCAL`
4. Start RabbitMQ: `docker-compose up -d rabbitmq`
5. Test locally!

### From Local to Azure

To deploy to Azure after local development:

1. Update `.env` with `ENVIRONMENT=AZURE`
2. Add Azure credentials to `.env`
3. Deploy as usual

The same codebase works for both!
