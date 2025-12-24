# Speech Processing API – Delivery Summary

## Scope
- **Design and document a production‑grade Speech Processing API exposing:**
  - **Unified Speech Pipeline** (Detect + Transcribe + Translate)
  - **Real-Time & Batch Text‑to‑Speech**
- **Target:**
  - Enterprise Banking/FSI (High Security)
  - Hybrid Whisper V3 Large + Azure Cognitive Services
  - **BYOS (Bring Your Own Storage)** with Identity-based access

---

## Key Outcomes

### 1) Architecture
- **Hybrid Async/Sync:**
  - **Async**: Heavy STT/Translation jobs (`/stt/process`).
  - **Sync**: Low-latency TTS streaming (`/tts/stream`).
- **Microservices:**
  - STT Orchestrator (Unified Pipeline)
  - TTS Service (Stream & Batch)
  - Job Service
- **Data:**
  - **Zero-Trust Storage**: API reads directly from customer containers via Managed Identity.

### 2) Security & Identity
- **OAuth2 Client Credentials** for API authentication.
- **Identity-Based Storage Access**:
  - **No SAS Tokens**.
  - API uses `DefaultAzureCredential` to access customer blobs.
  - Customers grant `Storage Blob Data Reader` to the API Identity.

### 3) API Surface
- **Unified Pipeline:**
  - `POST /stt/process` (The "Fire and Forget" endpoint)
- **Real-Time:**
  - `POST /tts/stream` (Binary audio stream)
- **Granular & Batch:**
  - `POST /speech-to-text/transcribe`
  - `POST /text-to-speech/synthesize`
- **Management:**
  - `GET /jobs/{job_id}`

### 4) Design Principles
- **Composite Operations**: Reduce client-side logic by chaining operations on the server.
- **Latency Aware**: Provide specific endpoints for specific latency needs (Stream vs Batch).
- **Security First**: Eliminate Shared Access Signatures (SAS) entirely.

---

## What You Can Do With This
- **Build Voice Bots**: Use `/tts/stream` for sub-second responses.
- **Process Archives**: Use `/stt/process` for massive backlogs of audio.
- **Secure Integration**: Integrate with banking storage without exposing SAS tokens.

---

## Recommended Next Steps

1. **Finalise Contracts**
   - Publish the updated OpenAPI 3.1 spec.

2. **Build Minimum Viable Platform**
   - Implement the `/stt/process` orchestrator.
   - Implement the `/tts/stream` endpoint.

3. **Security Hardening**
   - Test Managed Identity access across different Azure subscriptions (Cross-tenant BYOS).

---

## Strengths of This Design
- **Developer Experience**: "One call does it all" for transcription.
- **Performance**: Streaming TTS enables real-time conversation.
- **Security**: Best-in-class Azure Identity integration.
