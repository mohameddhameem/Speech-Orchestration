# Speech Processing API – Complete Documentation

## 0. Overview

This document is the single, merged reference for your Speech Processing API design. It combines:

- Executive summary and architecture overview
- Design decisions and Microsoft alignment
- Endpoint and data model overview (backed by a full OpenAPI 3.1 spec)
- Implementation and deployment guidance
- Quick reference for day‑to‑day development
- Role‑based navigation (architects, backend, frontend, DevOps)

The underlying API is specified formally in OpenAPI 3.1 for tooling, code generation, and validation.  
It follows modern REST design best practices (clear resources, consistent status codes, OAuth2, etc.). 

---

## 1. Executive Summary

### 1.1 Purpose

The Speech Processing API provides:

- **Speech‑to‑Text (STT)**  
  - Unified Pipeline (Detect + Transcribe + Translate)
  - Granular operations for specific tasks

- **Text‑to‑Speech (TTS)**  
  - **Real-time Streaming** (Low latency)
  - Batch Synthesis (High volume)

The design targets:

- Enterprise environments (banks/FSI)
- Hybrid model usage:
  - Self‑hosted Whisper V3 Large
  - Azure Cognitive Services as fallback/premium

### 1.2 Key Characteristics

- **Hybrid Async/Sync**: 
  - Heavy STT jobs are **Async** (`202 Accepted`).
  - Conversational TTS is **Sync** (`200 OK` stream).
- **Strong contracts**: Full OpenAPI 3.1 specification.
- **Secure by design**:
  - OAuth2 Client Credentials for API authentication.
  - **BYOS (Bring Your Own Storage)**: Zero-trust storage access via Managed Identity (No SAS tokens).
- **Cloud‑native**: Designed around Azure Blob Storage, managed identities, and queue‑based processing.

---

## 2. Architecture & Design Decisions

### 2.1 High‑Level Architecture

**Flow (logical):**

```
Client
→ OAuth2 Token Service (Client Credentials)
→ API Gateway (Auth, Rate Limits, Routing)
→ Speech API Services:
    - STT Service (Unified Pipeline)
    - TTS Service (Streaming & Batch)
    - Job Service (Status, Listing)
→ Job Queue (e.g., Azure Service Bus / RabbitMQ)
→ Workers:
    - Whisper V3 Workers (GPU)
    - Azure Speech/Translation Adapters
→ Azure Blob Storage (Customer Owned & Service Owned)
```

### 2.2 Major Design Decisions

**Decision 1 – Unified Pipeline**
- Instead of chaining multiple API calls (Detect -> Wait -> Transcribe -> Wait -> Translate), clients submit a single **Composite Job** (`/stt/process`).
- The server orchestrates the pipeline, reducing client complexity and latency.

**Decision 2 – Streaming First for TTS**
- Voice assistants require immediate audio. The `/tts/stream` endpoint provides a direct binary stream, bypassing the job queue for sub-second latency.

**Decision 3 – BYOS & Identity**
- **No SAS Tokens**: We do not accept SAS URLs.
- **Structured References**: Clients provide `storage_account`, `container`, and `blob_name`.
- **RBAC**: The Service Identity must be granted `Storage Blob Data Reader` on the customer's container.

---

## 3. API Specification & Endpoints (Conceptual)

### 3.1 Authentication

- **Scheme**: OAuth2 – Client Credentials.
- **Token endpoint**: `POST /oauth/token` (separate auth service).

### 3.2 Core Resources

**Jobs**
- **`job_id`**: Server‑generated UUID per job.
- Types: `composite`, `transcription`, `text_to_speech`.

### 3.3 Endpoints

#### Speech‑to‑Text

1. **`POST /stt/process` (Unified Pipeline)**
   - **Purpose**: "Fire and forget" detection, transcription, and translation.
   - **Input**: `BlobSource` (BYOS) + `Config` (languages, models).
   - **Output**: `202 Accepted` + `job_id`.

2. **`POST /speech-to-text/transcribe`**
   - **Purpose**: Direct upload for smaller files or granular control.

#### Text‑to‑Speech

3. **`POST /tts/stream` (Real-Time)**
   - **Purpose**: Immediate audio generation for chatbots.
   - **Output**: Binary audio stream (`audio/mpeg`).

4. **`POST /text-to-speech/synthesize` (Batch)**
   - **Purpose**: Long-form content generation.
   - **Output**: `202 Accepted` + `job_id`.

#### Job Management

5. **`GET /jobs/{job_id}`**
   - **Purpose**: Poll status. Returns final JSON results or download URLs.

---

## 4. Implementation Guide (Condensed)

### 4.1 Storage Access (BYOS)

- **Client Responsibility**:
  - Upload audio to their own Azure Container.
  - Grant `Storage Blob Data Reader` to the API's Managed Identity.
- **API Responsibility**:
  - Use `DefaultAzureCredential` to read the blob.
  - Process and store results in the API's own output container (or write back if permitted).

### 4.2 Processing Flow (Unified Pipeline)

1. Client uploads audio to `my-container`.
2. Client calls `/stt/process` with `{"storage_account": "my-account", "container": "my-container", ...}`.
3. API validates access using its Managed Identity.
4. Job is enqueued.
5. Worker pulls job, detects language (Whisper), transcribes (Whisper), translates (Azure).
6. Result is aggregated into a single JSON and stored.
7. Client polls `/jobs/{id}` and gets the full result.

---

## 5. Comparison with Microsoft Azure Speech

### 5.1 Alignment
- **Async operations**: Aligned with Azure Batch Transcription.
- **Streaming**: Aligned with Azure Speech SDK streaming (but via REST).

### 5.2 Simplifications & Extensions
- **Unified Job Model**: One endpoint for the entire workflow.
- **BYOS Security**: Enforced Managed Identity access, removing SAS token risks entirely.

---

## 6. Quick Reference (Cheat Sheet)

### 6.1 Endpoints at a Glance

```
POST /stt/process                  # Unified Pipeline (Detect+Transcribe+Translate)
POST /tts/stream                   # Real-time TTS
POST /speech-to-text/transcribe    # Direct upload STT
GET  /jobs/{job_id}                # Poll status
```

### 6.2 Example – Unified Pipeline

```bash
curl -X POST https://api.example.com/v1/stt/process \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "audio_source": {
      "type": "azure_blob",
      "storage_account_name": "clientdata",
      "container_name": "uploads",
      "blob_name": "file.wav"
    },
    "config": { "language": "auto" }
  }'
```

---

## 7. Role‑Based Navigation

### 7.1 Architects
Focus on **Section 2 (Unified Pipeline & BYOS)**.

### 7.2 Backend Engineers
Focus on **Section 4 (Storage Access)** and **OpenAPI Spec**.

### 7.3 Frontend / Client Developers
Focus on **Section 6 (Quick Reference)** and **Polling Strategy**.

---

## 8. Implementation Checklist (Condensed)

- [ ] Finalise OpenAPI 3.1 spec.
- [ ] Implement Unified Pipeline orchestrator.
- [ ] Implement Streaming TTS endpoint.
- [ ] Configure Managed Identity for BYOS access.
- [ ] Deploy Whisper GPU workers.

## 9. Limits & SLA Expectations

- **Payload limits**: Direct upload max 1GB (matches OpenAPI); prefer BYOS for large audio.
- **Rate limits**: 429 on exceed. Clients should back off starting at 1s, multiplier 1.5, cap 30s (same profile as `GET /jobs/{job_id}` guidance).
- **Job retention**: Results available for 7 days (`expires_at` / 410 after expiry).
- **Polling cadence**: Exponential backoff as above; avoid <1s polling to reduce queue pressure.
- **Streaming TTS**: Target p50 < 1.5s first-byte for <500 chars; if unmet, fall back to batch endpoint.
- **Availability**: Health at `/health` is unauthenticated for basic liveness; treat `degraded` as acceptable for retries, `unavailable` as trigger for circuit breaker.
