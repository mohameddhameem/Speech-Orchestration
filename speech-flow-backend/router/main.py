import asyncio
import json
import os
import sys
import httpx
from datetime import datetime, timezone

# Add parent directory to path to import database/models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import Job, JobStep
from config import settings
from sqlalchemy.orm import Session

# Import adapters for multi-environment support
try:
    from messaging_adapter import get_message_broker, ServiceBusMessage
    USE_ADAPTERS = True
except ImportError:
    from azure.servicebus.aio import ServiceBusClient
    from azure.servicebus import ServiceBusMessage
    USE_ADAPTERS = False

# Queue Names - Centralized from config
QUEUE_ROUTER = settings.ROUTER_QUEUE_NAME
QUEUE_LID = settings.LID_QUEUE_NAME
QUEUE_WHISPER = settings.WHISPER_QUEUE_NAME
QUEUE_AZURE = settings.AZURE_AI_QUEUE_NAME

MAX_RETRIES = 3


def _now_utc():
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc)


def _parse_iso_datetime(value):
    """Parse ISO datetime string to datetime object"""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except:
        return None


async def get_job(db: Session, job_id: str):
    return db.query(Job).filter(Job.job_id == job_id).first()


async def create_step(db: Session, job_id: str, step_name: str):
    """Create a new processing step with queue timestamp"""
    step = JobStep(
        job_id=job_id, 
        step_name=step_name, 
        status="QUEUED", 
        retry_count=0,
        queued_at=_now_utc()
    )
    db.add(step)
    db.commit()
    return step


async def get_latest_step(db: Session, job_id: str, step_name: str):
    return db.query(JobStep).filter(
        JobStep.job_id == job_id, 
        JobStep.step_name == step_name
    ).order_by(JobStep.queued_at.desc()).first()


async def update_step_with_metrics(db: Session, job_id: str, step_name: str, 
                                    status: str, result: dict = None, 
                                    metrics: dict = None, error: str = None):
    """
    Update step status and persist all metrics from workers.
    This is the central place where performance data gets recorded.
    """
    step = await get_latest_step(db, job_id, step_name)
    if not step:
        return None
    
    step.status = status
    step.error_message = error
    step.completed_at = _now_utc()
    
    # Store result payload
    if result:
        step.result_payload = result
    
    # Persist metrics from worker
    if metrics:
        # Timing metrics
        step.dequeued_at = _parse_iso_datetime(metrics.get("dequeued_at"))
        step.started_at = _parse_iso_datetime(metrics.get("started_at"))
        step.completed_at = _parse_iso_datetime(metrics.get("completed_at")) or step.completed_at
        step.queue_wait_ms = metrics.get("queue_wait_ms")
        step.processing_duration_ms = metrics.get("processing_duration_ms")
        
        # Worker identification
        step.worker_id = metrics.get("worker_id")
        step.worker_node = metrics.get("worker_node")
        step.worker_node_pool = metrics.get("worker_node_pool")
        
        # Model information
        step.model_name = metrics.get("model_name")
        step.model_version = metrics.get("model_version")
        
        # LID-specific metrics
        if metrics.get("detected_language"):
            step.detected_language = metrics.get("detected_language")
            step.language_confidence = metrics.get("language_confidence")
        
        # Transcription metrics
        if metrics.get("transcript_word_count"):
            step.transcript_word_count = metrics.get("transcript_word_count")
            step.transcript_char_count = metrics.get("transcript_char_count")
            step.transcription_rtf = metrics.get("transcription_rtf")
        
        # Azure OpenAI metrics
        if metrics.get("total_tokens"):
            step.prompt_tokens = metrics.get("prompt_tokens")
            step.completion_tokens = metrics.get("completion_tokens")
            step.total_tokens = metrics.get("total_tokens")
            step.api_cost_usd = metrics.get("api_cost_usd")
        
        # Error categorization
        if metrics.get("error_code"):
            step.error_code = metrics.get("error_code")
    
    db.commit()
    return step


async def update_job_aggregates(db: Session, job_id: str):
    """
    Update job-level aggregate metrics from steps.
    Called when job completes or fails.
    """
    job = await get_job(db, job_id)
    if not job:
        return
    
    # Get all completed steps
    steps = db.query(JobStep).filter(JobStep.job_id == job_id).all()
    
    # Aggregate token usage and cost
    total_tokens = sum(s.total_tokens or 0 for s in steps)
    total_cost = sum(float(s.api_cost_usd or 0) for s in steps)
    
    job.total_tokens_used = total_tokens
    job.total_cost_usd = total_cost
    job.completed_at = _now_utc()
    
    # Set source language from LID step if detected
    lid_step = next((s for s in steps if s.step_name == "LID" and s.detected_language), None)
    if lid_step:
        job.source_language = lid_step.detected_language
    
    db.commit()


async def dispatch_to_queue(sender, queue_name, message_body):
    """Dispatch message with queue timestamp for latency tracking"""
    message_body["queued_at"] = _now_utc().isoformat()
    message = ServiceBusMessage(json.dumps(message_body))
    await sender.get_queue_sender(queue_name).send_messages(message)
    print(f"Dispatched to {queue_name}: {message_body.get('job_id')}")


async def send_callback(job):
    """Send webhook callback on job completion/failure"""
    callback_url = job.callback_url or (job.metadata_ and job.metadata_.get("callback_url"))
    if not callback_url:
        return

    print(f"Sending callback to {callback_url} for Job {job.job_id}")
    payload = {
        "job_id": str(job.job_id),
        "status": job.status,
        "workflow_type": job.workflow_type,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "total_tokens_used": job.total_tokens_used,
        "total_cost_usd": float(job.total_cost_usd) if job.total_cost_usd else 0
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(callback_url, json=payload, timeout=10.0)
            # Update callback status
            job.callback_sent_at = _now_utc()
            job.callback_status = "success" if response.status_code < 400 else "failed"
    except Exception as e:
        print(f"Failed to send callback: {e}")
        job.callback_status = "failed"


async def process_router_message(msg_content, sb_client):
    db = SessionLocal()
    try:
        job_id = msg_content.get("job_id")
        event_type = msg_content.get("event")  # JOB_STARTED, STEP_COMPLETED, STEP_FAILED
        metrics = msg_content.get("metrics", {})
        result = msg_content.get("result", {})
        
        print(f"Processing event: {event_type} for Job {job_id}")
        
        job = await get_job(db, job_id)
        if not job:
            print(f"Job {job_id} not found")
            return

        sender = sb_client

        if event_type == "JOB_STARTED":
            job.status = "PROCESSING"
            job.started_at = _now_utc()
            job.queued_at = _now_utc()
            db.commit()
            
            # Initial Step: Always LID for full_pipeline
            if job.workflow_type == "full_pipeline" or job.workflow_type == "lid_only":
                await create_step(db, job_id, "LID")
                await dispatch_to_queue(sender, QUEUE_LID, {"job_id": job_id})
                
            elif job.workflow_type == "transcribe_only":
                lang = job.source_language or (job.metadata_ and job.metadata_.get("language")) or "en"
                await create_step(db, job_id, "TRANSCRIBE")
                
                if lang == "en":
                    await dispatch_to_queue(sender, QUEUE_AZURE, {"job_id": job_id, "task": "transcribe", "language": "en"})
                else:
                    await dispatch_to_queue(sender, QUEUE_WHISPER, {"job_id": job_id, "language": lang})

        elif event_type == "STEP_COMPLETED":
            step_name = msg_content.get("step_name")
            
            # Update step with all metrics
            await update_step_with_metrics(db, job_id, step_name, "COMPLETED", 
                                           result=result, metrics=metrics)
            
            if step_name == "LID":
                detected_lang = result.get("language")
                confidence = result.get("confidence", 0)
                print(f"LID Detected: {detected_lang} (confidence: {confidence})")
                
                if job.workflow_type == "lid_only":
                    job.status = "COMPLETED"
                    await update_job_aggregates(db, job_id)
                    await send_callback(job)
                    return

                await create_step(db, job_id, "TRANSCRIBE")
                
                if detected_lang == "en":
                    await dispatch_to_queue(sender, QUEUE_AZURE, {"job_id": job_id, "task": "transcribe", "language": "en"})
                else:
                    await dispatch_to_queue(sender, QUEUE_WHISPER, {"job_id": job_id, "language": detected_lang})

            elif step_name == "TRANSCRIBE":
                await create_step(db, job_id, "SUMMARIZE")
                transcript_text = result.get("text_preview", "")
                await dispatch_to_queue(sender, QUEUE_AZURE, {"job_id": job_id, "task": "summarize", "text": transcript_text})

            elif step_name == "SUMMARIZE" or step_name == "TRANSLATE":
                job.status = "COMPLETED"
                await update_job_aggregates(db, job_id)
                print(f"Job {job_id} COMPLETED")
                await send_callback(job)
        
        elif event_type == "STEP_FAILED":
            step_name = msg_content.get("step_name")
            error_msg = msg_content.get("error")
            print(f"Step {step_name} FAILED: {error_msg}")
            
            step = await get_latest_step(db, job_id, step_name)
            
            # Retry Logic
            if step and step.retry_count < MAX_RETRIES:
                step.retry_count += 1
                step.status = "QUEUED"
                step.queued_at = _now_utc()  # Reset queue time for retry
                
                # Store error info from failed attempt
                if metrics:
                    step.error_code = metrics.get("error_code")
                    step.processing_duration_ms = metrics.get("processing_duration_ms")
                
                db.commit()
                print(f"Retrying step {step_name} (Attempt {step.retry_count}/{MAX_RETRIES})")
                
                # Re-dispatch based on step name
                if step_name == "LID":
                    await dispatch_to_queue(sender, QUEUE_LID, {"job_id": job_id})
                    
                elif step_name == "TRANSCRIBE":
                    # Get language from LID result or job metadata
                    lid_step = await get_latest_step(db, job_id, "LID")
                    lang = "en"
                    if lid_step and lid_step.detected_language:
                        lang = lid_step.detected_language
                    elif job.source_language:
                        lang = job.source_language
                    elif job.metadata_ and job.metadata_.get("language"):
                        lang = job.metadata_.get("language")
                    
                    if lang == "en":
                        await dispatch_to_queue(sender, QUEUE_AZURE, {"job_id": job_id, "task": "transcribe", "language": "en"})
                    else:
                        await dispatch_to_queue(sender, QUEUE_WHISPER, {"job_id": job_id, "language": lang})
                        
                elif step_name == "SUMMARIZE":
                    transcribe_step = await get_latest_step(db, job_id, "TRANSCRIBE")
                    if transcribe_step and transcribe_step.result_payload:
                        text_preview = transcribe_step.result_payload.get("text_preview", "")
                        await dispatch_to_queue(sender, QUEUE_AZURE, {"job_id": job_id, "task": "summarize", "text": text_preview})
                    else:
                        await update_step_with_metrics(db, job_id, step_name, "FAILED", 
                                                       error="Cannot retry: missing transcript data",
                                                       metrics=metrics)
                        job.status = "FAILED"
                        await update_job_aggregates(db, job_id)
                        await send_callback(job)

            else:
                # Max retries exceeded
                await update_step_with_metrics(db, job_id, step_name, "FAILED", 
                                               error=error_msg, metrics=metrics)
                job.status = "FAILED"
                await update_job_aggregates(db, job_id)
                await send_callback(job)

    except Exception as e:
        print(f"Error processing message: {e}")
    finally:
        db.close()


async def main():
    print("Starting Router Service...")
    conn_str = settings.SERVICEBUS_CONNECTION_STRING if settings.ENVIRONMENT == "AZURE" else settings.RABBITMQ_URL
    queue_name = settings.ROUTER_QUEUE_NAME

    if USE_ADAPTERS:
        # Explicitly pass as connection_string to avoid positional mismatch
        async with get_message_broker(connection_string=conn_str) as client:
            receiver = await client.get_queue_receiver(queue_name=queue_name)
            async with receiver:
                print(f"Listening on {queue_name}...")
                async for msg in receiver:
                    body = json.loads(str(msg))
                    await process_router_message(body, client)
                    await receiver.complete_message(msg)
    else:
        from azure.servicebus.aio import ServiceBusClient
        async with ServiceBusClient.from_connection_string(conn_str) as client:
            receiver = client.get_queue_receiver(queue_name=queue_name)
            async with receiver:
                print(f"Listening on {queue_name}...")
                async for msg in receiver:
                    body = json.loads(str(msg))
                    await process_router_message(body, client)
                    await receiver.complete_message(msg)


if __name__ == "__main__":
    asyncio.run(main())
