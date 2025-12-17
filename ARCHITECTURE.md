# Application Architecture & Design

This document details the internal software architecture, data models, and workflow logic of the Speech Flow system. For infrastructure and deployment details, see [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md).

## 1. Component Specifications

### 1.1 Backend Services (`speech-flow-backend`)

#### API Gateway (`/api/main.py`)
- **Role:** Entry point for all client interactions.
- **Key Features:**
  - Generates SAS Tokens for direct-to-blob uploads.
  - Validates workflows using `Literal` types.
  - Aggregates results from Blob Storage.

#### Router Service (`/router/main.py`)
- **Role:** Central orchestrator consuming `job-events` queue.
- **Logic:** State machine that dispatches jobs to specific worker queues based on workflow type and current step status.
- **Retry Policy:** Exponential backoff with configurable `MAX_RETRIES`.

### 1.2 Workers (`speech-flow-workers`)

#### BaseWorker (`/common/base_worker.py`)
- **Abstract Class:** Provides common functionality for all workers.
- **Features:**
  - **Idempotency:** Checks `processing_steps` table before starting work.
  - **Graceful Shutdown:** Handles SIGTERM/SIGINT.
  - **Blob/DB Adapters:** Standardized I/O.

#### Specific Workers
- **LID Worker:** Uses Facebook MMS (`facebook/mms-lid-126`) on CPU.
- **Whisper Worker:** Uses `faster-whisper` (CTranslate2) on GPU/CPU.
- **Azure AI Worker:** Uses Azure OpenAI (GPT-4) for translation and summarization.

## 2. Workflow Definitions

The system supports flexible workflows defined by the `workflow_type` parameter:

1.  **Full Pipeline:** `LID` -> `TRANSCRIBE` -> `TRANSLATE` (if needed) -> `SUMMARIZE`
2.  **Transcribe Only:** `TRANSCRIBE` (requires source language)
3.  **LID Only:** `LID`
4.  **Translate Only:** `TRANSLATE` (requires transcript)
5.  **Summarize Only:** `SUMMARIZE` (requires transcript)

## 3. Database Schema

The system uses PostgreSQL with two main tables:

### `jobs`
Tracks the overall job status and metadata.
- `id`: UUID
- `status`: `pending_upload`, `queued`, `processing`, `completed`, `failed`
- `workflow_type`: The selected pipeline.

### `processing_steps`
Tracks individual steps within a job.
- `job_id`: FK to `jobs`
- `step_type`: `LID`, `TRANSCRIBE`, `TRANSLATE`, `SUMMARIZE`
- `status`: `pending`, `processing`, `completed`, `failed`
- `retry_count`: For error handling.

## 4. Reliability Patterns

- **Idempotency:** Workers check if a step is already completed before processing.
- **Retries:** The Router re-queues failed steps up to `MAX_RETRIES`.
- **Dead Letter Queues:** Azure Service Bus handles messages that fail repeatedly (configured in infrastructure).

