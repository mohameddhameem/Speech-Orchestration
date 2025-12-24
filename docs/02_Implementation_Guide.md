# Speech Processing API - Implementation Guide

## Executive Summary

Your Speech Processing API exposes enterprise-grade speech services with:
- **Self-hosted Whisper V3 Large** for cost-efficient transcription at scale
- **Azure Cognitive Services** for fallback/premium features (language-specific models, enhanced quality)
- **Hybrid Architecture**:
  - **Async-first** for batch processing (Unified Pipeline)
  - **Synchronous Streaming** for real-time TTS
- **OAuth2 + DefaultAzureCredential** for secure, scalable file handling (BYOS - Bring Your Own Storage)
- **OpenAPI 3.1 specification** for SDK generation and multi-language client support

---

## Architecture Overview

### Technology Stack

```
Client Layer
    ↓ OAuth2 Token (Bearer)
API Gateway (Kong / Azure API Management)
    ├─→ STT Service (Unified Pipeline & Granular)
    └─→ TTS Service (Stream & Batch)
         ↓
    ┌────────────────────┬──────────────┬──────────────┐
    ↓                    ↓              ↓              ↓
Whisper V3 Large   Azure Speech    Job Queue      Blob Storage
(Self-hosted)      (Fallback)      (RabbitMQ)     (BYOS Containers)
    ↓                    ↓              ↓              ↓
   GPU Cluster      Cloud Compute   Workers        Managed Identity
```

### Key Design Decisions

1. **Unified Pipeline ("Fire and Forget")**:
   - Single endpoint `/stt/process` handles Detection → Transcription → Translation.
   - Reduces client-side orchestration and state management.

2. **Real-Time & Batch Modes**:
   - **STT**: Always Async (Job-based) for reliability.
   - **TTS**: 
     - `/tts/stream`: Synchronous low-latency audio for voice bots.
     - `/text-to-speech/synthesize`: Async for long-form content.

3. **Bring Your Own Storage (BYOS)**:
   - **Zero-Trust Storage**: API never accepts large file uploads directly.
   - **Structured References**: Clients pass `storage_account`, `container`, and `blob_name`.
   - **Security**: API uses Managed Identity to read from customer containers (requires `Storage Blob Data Reader` role).

---

## API Endpoints Summary

### Speech-to-Text (STT)

| Endpoint | Method | Mode | Purpose |
|----------|--------|------|---------|
| `/stt/process` | POST | Async | **Unified Pipeline** (Detect + Transcribe + Translate) |
| `/speech-to-text/transcribe` | POST | Async | Granular Transcription (Direct Upload) |
| `/speech-to-text/detect-language` | POST | Async | Granular Detection |
| `/speech-to-text/translate` | POST | Async | Granular Translation |

### Text-to-Speech (TTS)

| Endpoint | Method | Mode | Purpose |
|----------|--------|------|---------|
| `/tts/stream` | POST | **Sync** | **Real-time** audio stream (Chatbots) |
| `/text-to-speech/synthesize` | POST | Async | Batch synthesis (Audiobooks/Articles) |

### Job Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/jobs/{job_id}` | GET | Poll job status |
| `/jobs` | GET | List jobs with filters |
| `/health` | GET | Service health |
| `/available-voices` | GET | List TTS voices |

---

## Request/Response Examples

### Example 1: Unified Pipeline (BYOS)

**Request:**
```bash
curl -X POST https://api.speechapi.dev/v1/stt/process \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_source": {
      "type": "azure_blob",
      "storage_account_name": "customerdata",
      "container_name": "audio-uploads",
      "blob_name": "meetings/2024/q1_review.wav"
    },
    "config": {
      "language": "auto", 
      "model": "whisper-large-v3",
      "translation": {
        "target_languages": ["es-ES", "de-DE"]
      },
      "diarization": {
        "enabled": true
      }
    }
  }'
```

**Response (202 Accepted):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2025-12-20T21:50:00Z",
  "estimated_wait_minutes": 5
}
```

---

### Example 2: Real-Time TTS Streaming

**Request:**
```bash
curl -X POST https://api.speechapi.dev/v1/tts/stream \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how can I help you today?",
    "language": "en-US",
    "voice_id": "en-US-AriaNeural",
    "audio_format": "mp3"
  }' --output response.mp3
```

**Response (200 OK):**
- **Headers**: `Content-Type: audio/mpeg`
- **Body**: Binary audio data (streamed)

---

### Example 3: Poll Job Status

**Request:**
```bash
curl -X GET https://api.speechapi.dev/v1/jobs/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response (200 OK - Completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "language": "en-US",
  "text": "Welcome to the meeting...",
  "translations": {
    "es-ES": "Bienvenido a la reunión...",
    "de-DE": "Willkommen beim Treffen..."
  },
  "download_url": "https://speechapi.blob.core.windows.net/results/550e8400.json"
}
```

---

## Authentication & Security

### 1. API Authentication (OAuth2)
Clients authenticate via Client Credentials flow to obtain a Bearer token.

### 2. Storage Security (BYOS + Managed Identity)
We do **not** use SAS tokens. Instead, we use Azure RBAC.

**Customer Setup Steps:**
1. Create an Azure Storage Account.
2. Create a container (e.g., `audio-input`).
3. Grant our **Service Principal ID** (provided during onboarding) the **Storage Blob Data Reader** role on that container.
4. Send requests with the `storage_account_name`, `container_name`, and `blob_name`.

**Backend Implementation (Python):**
```python
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

def get_blob_stream(account_name, container, blob_name):
    # Uses the API's Managed Identity
    credential = DefaultAzureCredential()
    account_url = f"https://{account_name}.blob.core.windows.net"
    
    blob_service_client = BlobServiceClient(account_url, credential=credential)
    blob_client = blob_service_client.get_blob_client(container=container, blob=blob_name)
    
    return blob_client.download_blob().readall()
```

---

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "ACCESS_DENIED",
    "message": "Could not access blob. Ensure 'Storage Blob Data Reader' role is assigned.",
    "details": {
      "container": "audio-uploads"
    }
  },
  "request_id": "..."
}
```

### Common Codes
| Code | Description |
|------|-------------|
| `ACCESS_DENIED` | Service Identity cannot read the customer blob. |
| `INVALID_CONFIG` | Incompatible model/language combination. |
| `QUOTA_EXCEEDED` | Monthly audio limit reached. |

---

## SDK Generation
Use the updated `openapi.yaml` to generate clients:
```bash
openapi-generator-cli generate -i specs/openapi.yaml -g python -o ./sdk/python
```
