# Local Development Mode - README Section

Add this section to your main README.md file:

---

## 🏠 Local Development Mode

The Speech Orchestration system now supports **complete local development** without any Azure dependencies!

### Quick Start - Local Mode

```bash
# Clone the repository
git clone https://github.com/mohameddhameem/Speech-Orchestration.git
cd Speech-Orchestration

# Start all services in local mode (one command!)
docker-compose -f docker-compose.yaml -f docker-compose.local.yml up -d

# Access the services
open http://localhost:8000/docs        # API (Swagger UI)
open http://localhost:8501             # Dashboard
open http://localhost:15672            # RabbitMQ Management (guest/guest)
```

### What's Different in Local Mode?

When running locally (`ENVIRONMENT=LOCAL`), the system uses:

| Component | Production (Azure) | Local Development |
|-----------|-------------------|-------------------|
| Message Queue | Azure Service Bus | **RabbitMQ** |
| Storage | Azure Blob Storage | **Local Filesystem** |
| AI Models | Azure OpenAI (GPT-4) | **HuggingFace** (BART, OPUS-MT) |

### Benefits of Local Mode

- ✅ **Zero Cost** - No Azure bills during development
- ✅ **Offline Work** - Develop without internet (after initial setup)
- ✅ **Full Privacy** - All data stays on your machine
- ✅ **Fast Iteration** - Quick startup and testing
- ✅ **Easy Debugging** - All services accessible locally

### Models Used in Local Mode

- **Summarization**: `facebook/bart-large-cnn` (~1.6GB)
  - Good quality general summarization
  - ~2-5 seconds per summary on CPU

- **Translation**: `Helsinki-NLP/opus-mt-{src}-{tgt}` (~300MB each)
  - Good quality for common language pairs
  - ~1-3 seconds per translation on CPU
  - Fallback to NLLB-200 for unsupported pairs

### Switching Between Modes

**Local Development:**
```bash
docker-compose -f docker-compose.yaml -f docker-compose.local.yml up -d
```

**Azure Production:**
```bash
# Set up .env with Azure credentials
ENVIRONMENT=AZURE
AZURE_STORAGE_CONNECTION_STRING=...
SERVICEBUS_CONNECTION_STRING=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_KEY=...

docker-compose up -d
```

### Documentation

- 📖 **[Local Development Guide](LOCAL_DEVELOPMENT.md)** - Complete setup instructions
- 📖 **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Technical details
- 📖 **[Implementation Complete](IMPLEMENTATION_COMPLETE.md)** - Feature overview

### Requirements

- Docker and Docker Compose
- 8GB RAM (16GB recommended for workers)
- 10GB free disk space (for models)

### Testing Your Setup

```bash
# Run the test script
python3 test_local_setup.py

# Submit a test job
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"audio_filename": "test.wav", "workflow_type": "full_pipeline"}'
```

---
