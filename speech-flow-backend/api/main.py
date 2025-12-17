"""
Speech Flow API Gateway
Handles job submission, status checks, and result retrieval
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Literal, Optional

from config import settings
from database import get_db
from fastapi import Depends, FastAPI, HTTPException, Query
from models import Job, JobStep
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

# Import adapters for multi-environment support
try:
    from messaging_adapter import ServiceBusMessage, get_message_broker
    from storage_adapter import get_storage_adapter

    USE_ADAPTERS = True
except ImportError:
    # Fallback to direct Azure imports
    from azure.servicebus import ServiceBusClient, ServiceBusMessage
    from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas

    USE_ADAPTERS = False


app = FastAPI(title="Speech Flow API", description="Event-driven speech processing pipeline", version="1.0.0")


# ============== Request/Response Models ==============


class JobSubmitRequest(BaseModel):
    """Request model for job submission"""

    audio_filename: str = Field(..., description="Name of the audio file to process")
    workflow_type: Literal["full_pipeline", "transcribe_only", "lid_only", "translate_only", "summarize_only"] = Field(
        default="full_pipeline", description="Type of processing workflow"
    )
    source_language: Optional[str] = Field(None, description="Source language code (e.g., 'en', 'zh', 'yue')")
    target_language: Optional[str] = Field(default="en", description="Target language for translation")
    callback_url: Optional[str] = Field(None, description="Webhook URL for completion notification")

    @model_validator(mode="after")
    def validate_workflow_requirements(self):
        """Validate that workflow-specific requirements are met"""
        if self.workflow_type == "transcribe_only" and not self.source_language:
            raise ValueError("transcribe_only workflow requires source_language to be specified")
        if self.workflow_type == "translate_only" and not self.source_language:
            raise ValueError("translate_only workflow requires source_language to be specified")
        if self.workflow_type == "summarize_only" and not self.source_language:
            raise ValueError("summarize_only workflow requires source_language to be specified")
        return self


class JobResponse(BaseModel):
    """Response model for job operations"""

    job_id: str
    status: str
    message: str
    upload_url: Optional[str] = None


class StepStatus(BaseModel):
    """Status of a single processing step"""

    step_type: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class JobStatusResponse(BaseModel):
    """Detailed job status response"""

    job_id: str
    status: str
    workflow_type: str
    audio_filename: str
    source_language: Optional[str]
    target_language: Optional[str]
    created_at: datetime
    updated_at: datetime
    steps: List[StepStatus]


class TranscriptionResult(BaseModel):
    """Transcription result data"""

    language: str
    text: str
    segments: Optional[List[dict]] = None


class TranslationResult(BaseModel):
    """Translation result data"""

    source_language: str
    target_language: str
    original_text: str
    translated_text: str


class SummaryResult(BaseModel):
    """Summary result data"""

    summary: str
    key_points: Optional[List[str]] = None


class JobResultsResponse(BaseModel):
    """Aggregated job results response"""

    job_id: str
    status: str
    workflow_type: str
    audio_filename: str
    detected_language: Optional[str] = None
    transcription: Optional[TranscriptionResult] = None
    translation: Optional[TranslationResult] = None
    summary: Optional[SummaryResult] = None
    completed_at: Optional[datetime] = None


# ============== Blob Storage Helpers ==============


def get_storage_client():
    """Get storage client (adapter or Azure Blob Service)"""
    if USE_ADAPTERS:
        return get_storage_adapter(settings.AZURE_STORAGE_CONNECTION_STRING)
    else:
        from azure.storage.blob import BlobServiceClient

        return BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)


def generate_upload_sas_url(job_id: str, filename: str) -> str:
    """Generate a SAS URL for uploading audio file.
    For Azurite/local development, ensure the URL points to the local BlobEndpoint,
    and use an API version compatible with Azurite.
    """
    container_name = settings.BLOB_CONTAINER_NAME
    blob_name = f"{job_id}/{filename}"

    if USE_ADAPTERS:
        storage = get_storage_adapter(settings.AZURE_STORAGE_CONNECTION_STRING)
        return storage.generate_upload_url(container_name, blob_name)
    else:
        from azure.storage.blob import (
            AccountSasPermissions,
            BlobSasPermissions,
            BlobServiceClient,
            ResourceTypes,
            generate_blob_sas,
        )

        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)

        # For Azurite, we need to be explicit about the endpoint
        is_azurite = blob_service_client.account_name == "devstoreaccount1"

        if is_azurite:
            # For Azurite, use localhost endpoint accessible from host
            base_url = "http://localhost:10000/devstoreaccount1"
        else:
            # For Azure Storage, use standard endpoint
            base_url = blob_service_client.url.rstrip("/")

        # Generate SAS token with parameters Azurite supports
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(write=True, create=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        return f"{base_url}/{container_name}/{blob_name}?{sas_token}"


def read_blob_json(container_name: str, blob_name: str) -> Optional[dict]:
    """Read JSON content from a blob"""
    try:
        if USE_ADAPTERS:
            storage = get_storage_adapter(settings.AZURE_STORAGE_CONNECTION_STRING)
            if storage.blob_exists(container_name, blob_name):
                content = storage.download_blob(container_name, blob_name)
                return json.loads(content.decode("utf-8"))
        else:
            from azure.storage.blob import BlobServiceClient

            blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
            container_client = blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)

            if blob_client.exists():
                content = blob_client.download_blob().readall()
                return json.loads(content.decode("utf-8"))
    except Exception:
        pass
    return None


# ============== Service Bus Helpers ==============


def send_job_event(
    job_id: str,
    workflow_type: str,
    audio_path: str,
    source_language: Optional[str],
    target_language: str,
    callback_url: Optional[str],
):
    """Send job event to the router queue"""
    message_body = {
        "job_id": job_id,
        "event_type": "JOB_CREATED",
        "workflow_type": workflow_type,
        "audio_blob_path": audio_path,
        "source_language": source_language,
        "target_language": target_language,
        "callback_url": callback_url,
        "timestamp": datetime.utcnow().isoformat(),
    }

    message = ServiceBusMessage(body=json.dumps(message_body), message_id=job_id, subject="JOB_CREATED")

    if USE_ADAPTERS and settings.ENVIRONMENT == "LOCAL":
        # Use RabbitMQ for local mode (synchronous version)
        try:
            import pika

            params = pika.URLParameters(settings.RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            queue_name = settings.ROUTER_QUEUE_NAME
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=json.dumps(message_body),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            connection.close()
        except Exception as e:
            # In LOCAL mode without RabbitMQ, log and continue
            # Job will remain in 'queued' status until manually processed
            print(f"Warning: Could not send job event to RabbitMQ: {e}")
            print(f"Job {job_id} queued but will not be processed without message broker")
    else:
        # Use Azure Service Bus
        from azure.servicebus import ServiceBusClient

        conn_str = settings.SERVICEBUS_CONNECTION_STRING
        with ServiceBusClient.from_connection_string(conn_str) as client:
            sender = client.get_queue_sender(queue_name=settings.ROUTER_QUEUE_NAME)
            with sender:
                sender.send_messages(message)


# ============== API Endpoints ==============


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "speech-flow-api"}


@app.post("/jobs", response_model=JobResponse)
async def submit_job(request: JobSubmitRequest, db: Session = Depends(get_db)):
    """
    Submit a new speech processing job.

    Returns a SAS URL for uploading the audio file.
    After upload, call POST /jobs/{job_id}/start to begin processing.
    """
    job_id = str(uuid.uuid4())

    # Create job record
    job = Job(
        job_id=job_id,
        customer_id="default",  # Default customer ID for simple UI
        audio_filename=request.audio_filename,
        workflow_type=request.workflow_type,
        source_language=request.source_language,
        target_language=request.target_language,
        callback_url=request.callback_url,
        status="pending_upload",
    )

    db.add(job)
    db.commit()

    # Generate upload URL
    upload_url = generate_upload_sas_url(job_id, request.audio_filename)

    return JobResponse(
        job_id=job_id,
        status="pending_upload",
        message="Upload audio file using the provided URL, then call POST /jobs/{job_id}/start",
        upload_url=upload_url,
    )


@app.post("/jobs/{job_id}/start", response_model=JobResponse)
async def start_job(job_id: str, db: Session = Depends(get_db)):
    """
    Start processing a job after audio file has been uploaded.
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "pending_upload":
        raise HTTPException(status_code=400, detail=f"Job cannot be started. Current status: {job.status}")

    # Verify audio file exists in blob storage
    blob_path = f"{job_id}/{job.audio_filename}"

    if USE_ADAPTERS:
        storage = get_storage_adapter(settings.AZURE_STORAGE_CONNECTION_STRING)
        blob_exists = storage.blob_exists(settings.BLOB_CONTAINER_NAME, blob_path)
    else:
        from azure.storage.blob import BlobServiceClient

        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(settings.BLOB_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(blob_path)
        blob_exists = blob_client.exists()

    if not blob_exists:
        raise HTTPException(status_code=400, detail="Audio file not found. Please upload the file first.")

    # Update job status
    job.status = "queued"
    job.updated_at = datetime.utcnow()
    db.commit()

    # Send event to router
    send_job_event(
        job_id=job_id,
        workflow_type=job.workflow_type,
        audio_path=blob_path,
        source_language=job.source_language,
        target_language=job.target_language,
        callback_url=job.callback_url,
    )

    return JobResponse(job_id=job_id, status="queued", message="Job submitted for processing")


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get detailed status of a job including all processing steps.
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get processing steps
    steps = db.query(JobStep).filter(JobStep.job_id == job_id).all()

    step_statuses = [
        StepStatus(
            step_type=step.step_name,
            status=step.status,
            started_at=step.started_at,
            completed_at=step.completed_at,
            error_message=step.error_message,
            retry_count=step.retry_count,
        )
        for step in steps
    ]

    return JobStatusResponse(
        job_id=str(job.job_id),
        status=job.status,
        workflow_type=job.workflow_type,
        audio_filename=job.audio_filename,
        source_language=job.source_language,
        target_language=job.target_language,
        created_at=job.created_at,
        updated_at=job.updated_at,
        steps=step_statuses,
    )


@app.get("/jobs/{job_id}/results", response_model=JobResultsResponse)
async def get_job_results(job_id: str, db: Session = Depends(get_db)):
    """
    Get aggregated results for a completed job.

    Returns transcription, translation, and summary results from blob storage.
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in ["completed", "partial_complete"]:
        raise HTTPException(status_code=400, detail=f"Results not available. Job status: {job.status}")

    # Get processing steps to find completed ones
    steps = db.query(JobStep).filter(JobStep.job_id == job_id).all()
    completed_steps = {step.step_name: step for step in steps if step.status == "completed"}

    # Build results response
    results = JobResultsResponse(
        job_id=str(job.job_id), status=job.status, workflow_type=job.workflow_type, audio_filename=job.audio_filename
    )

    # Get LID result
    if "LID" in completed_steps:
        lid_result = read_blob_json(settings.RESULTS_CONTAINER_NAME, f"{job_id}/lid_result.json")
        if lid_result:
            results.detected_language = lid_result.get("detected_language")

    # Get transcription result
    if "TRANSCRIBE" in completed_steps:
        transcription_result = read_blob_json(settings.RESULTS_CONTAINER_NAME, f"{job_id}/transcription.json")
        if transcription_result:
            results.transcription = TranscriptionResult(
                language=transcription_result.get("language", "unknown"),
                text=transcription_result.get("text", ""),
                segments=transcription_result.get("segments"),
            )

    # Get translation result
    if "TRANSLATE" in completed_steps:
        translation_result = read_blob_json(settings.RESULTS_CONTAINER_NAME, f"{job_id}/translation.json")
        if translation_result:
            results.translation = TranslationResult(
                source_language=translation_result.get("source_language", ""),
                target_language=translation_result.get("target_language", ""),
                original_text=translation_result.get("original_text", ""),
                translated_text=translation_result.get("translated_text", ""),
            )

    # Get summary result
    if "SUMMARIZE" in completed_steps:
        summary_result = read_blob_json(settings.RESULTS_CONTAINER_NAME, f"{job_id}/summary.json")
        if summary_result:
            results.summary = SummaryResult(
                summary=summary_result.get("summary", ""), key_points=summary_result.get("key_points")
            )

    # Get completion time from last completed step
    if completed_steps:
        last_completed = max((s.completed_at for s in completed_steps.values() if s.completed_at), default=None)
        results.completed_at = last_completed

    # Also check source language from job if not from LID
    if not results.detected_language and job.source_language:
        results.detected_language = job.source_language

    return results


@app.get("/jobs")
async def list_jobs(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    workflow_type: Optional[str] = Query(None, description="Filter by workflow type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
):
    """
    List jobs with optional filtering.
    """
    query = db.query(Job)

    if status:
        query = query.filter(Job.status == status)
    if workflow_type:
        query = query.filter(Job.workflow_type == workflow_type)

    total = query.count()
    jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "jobs": [
            {
                "job_id": str(job.job_id),
                "status": job.status,
                "workflow_type": job.workflow_type,
                "audio_filename": job.audio_filename,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
            }
            for job in jobs
        ],
    }


@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """
    Cancel a pending or queued job.
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job with status: {job.status}")

    job.status = "cancelled"
    job.updated_at = datetime.utcnow()
    db.commit()

    return {"job_id": job_id, "status": "cancelled", "message": "Job cancelled successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
