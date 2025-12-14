"""Base worker class for speech processing pipeline.

This module provides the foundation for all worker services in the speech processing
pipeline, handling message queue operations, storage operations, metrics collection,
and error handling.
"""

import os
import json
import asyncio
import signal
import socket
import time
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

# Add parent directory to path for backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'speech-flow-backend'))

# Import adapters
try:
    from messaging_adapter import get_message_broker, ServiceBusMessage
    from storage_adapter import get_storage_adapter
    USE_ADAPTERS = True
except ImportError:
    # Fallback to direct Azure imports if adapters not available
    from azure.servicebus.aio import ServiceBusClient
    from azure.servicebus import ServiceBusMessage
    from azure.storage.blob import BlobServiceClient
    USE_ADAPTERS = False


@dataclass
class StepMetrics:
    """Metrics collected during step processing for performance analysis.
    
    Attributes:
        queued_at: Timestamp when message was queued
        dequeued_at: Timestamp when message was dequeued
        started_at: Timestamp when processing started
        completed_at: Timestamp when processing completed
        queue_wait_ms: Time spent waiting in queue (milliseconds)
        processing_duration_ms: Time spent processing (milliseconds)
        worker_id: Unique identifier for the worker instance
        worker_node: Node name where worker is running
        worker_node_pool: Node pool name for worker
        model_name: Name of the model used for processing
        model_version: Version of the model used
        detected_language: Language detected (LID worker)
        language_confidence: Confidence score for language detection
        transcript_word_count: Number of words in transcript
        transcript_char_count: Number of characters in transcript
        transcription_rtf: Real-time factor for transcription
        audio_duration_seconds: Duration of audio file
        prompt_tokens: Number of prompt tokens (AI worker)
        completion_tokens: Number of completion tokens (AI worker)
        total_tokens: Total tokens used (AI worker)
        api_cost_usd: API cost in USD (AI worker)
        error_code: Error code if processing failed
        error_message: Error message if processing failed
    """
    
    # Timing metrics
    queued_at: Optional[datetime] = None
    dequeued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    queue_wait_ms: Optional[int] = None
    processing_duration_ms: Optional[int] = None
    
    # Worker info
    worker_id: Optional[str] = None
    worker_node: Optional[str] = None
    worker_node_pool: Optional[str] = None
    
    # Model info
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    
    # LID metrics
    detected_language: Optional[str] = None
    language_confidence: Optional[float] = None
    
    # Transcription metrics
    transcript_word_count: Optional[int] = None
    transcript_char_count: Optional[int] = None
    transcription_rtf: Optional[float] = None
    audio_duration_seconds: Optional[float] = None
    
    # AI model metrics
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    api_cost_usd: Optional[float] = None
    
    # Error info
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary with proper serialization.
        
        Returns:
            Dictionary with metrics, datetime values converted to ISO format
        """
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif value is not None:
                result[key] = value
        return result


class BaseWorker(ABC):
    """Base class for all workers in the speech processing pipeline.
    
    Provides common functionality for:
    - Message queue operations (Azure Service Bus or RabbitMQ)
    - Blob storage operations (Azure Blob or local filesystem)
    - Error handling and reporting
    - Graceful shutdown
    - Idempotency checks
    - Performance metrics collection
    
    Subclasses must implement the `process()` method to define
    worker-specific processing logic.
    """
    
    # Cost per 1000 tokens for Azure OpenAI (configurable via env vars)
    COST_PER_1K_INPUT_TOKENS: float = float(os.getenv("AZURE_OPENAI_INPUT_COST", "0.01"))
    COST_PER_1K_OUTPUT_TOKENS: float = float(os.getenv("AZURE_OPENAI_OUTPUT_COST", "0.03"))
    
    def __init__(self, queue_name: str, step_name: str):
        """Initialize worker with queue and step configuration.
        
        Args:
            queue_name: Name of the message queue to process
            step_name: Name of the processing step (e.g., "LID", "TRANSCRIBE")
        """
        self.queue_name = queue_name
        self.step_name = step_name
        self.running = True
        
        # Configuration from environment
        self.servicebus_conn_str: str = os.getenv("SERVICEBUS_CONNECTION_STRING", "")
        self.storage_conn_str: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
        self.blob_container_raw: str = os.getenv("BLOB_CONTAINER_NAME", "raw-audio")
        self.blob_container_results: str = os.getenv("BLOB_CONTAINER_RESULTS", "results")
        self.router_queue: str = os.getenv("ROUTER_QUEUE_NAME", "job-events")
        
        # Database connection for idempotency checks
        self.db_url: str = os.getenv("DATABASE_URL", "")
        
        # Worker identification
        self.worker_id: str = os.getenv("HOSTNAME", socket.gethostname())
        self.worker_node: str = os.getenv("NODE_NAME", "unknown")
        self.worker_node_pool: str = os.getenv("NODE_POOL", "default")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._shutdown_handler)
        signal.signal(signal.SIGINT, self._shutdown_handler)
    
    def _shutdown_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals for graceful termination.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        print(f"Received shutdown signal. Finishing current job...")
        self.running = False
    
    def _now_utc(self) -> datetime:
        """Get current UTC timestamp.
        
        Returns:
            Current datetime in UTC
        """
        return datetime.now(timezone.utc)
    
    def _calculate_api_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate Azure OpenAI API cost based on token usage.
        
        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
            
        Returns:
            Cost in USD, rounded to 6 decimal places
        """
        input_cost = (prompt_tokens / 1000) * self.COST_PER_1K_INPUT_TOKENS
        output_cost = (completion_tokens / 1000) * self.COST_PER_1K_OUTPUT_TOKENS
        return round(input_cost + output_cost, 6)
    
    def download_audio(self, blob_name: str, local_path: str) -> int:
        """Download audio file from blob storage.
        
        Args:
            blob_name: Name of the blob/file in storage
            local_path: Local path where file should be saved
            
        Returns:
            Size of downloaded file in bytes
        """
        if USE_ADAPTERS:
            storage = get_storage_adapter(self.storage_conn_str)
            data = storage.download_blob(self.blob_container_raw, blob_name)
        else:
            blob_service_client = BlobServiceClient.from_connection_string(self.storage_conn_str)
            blob_client = blob_service_client.get_blob_client(
                container=self.blob_container_raw, 
                blob=blob_name
            )
            data = blob_client.download_blob().readall()
        
        with open(local_path, "wb") as download_file:
            download_file.write(data)
        return len(data)
    
    def upload_result(self, job_id: str, suffix: str, result_data: dict) -> str:
        """Upload result JSON to blob storage"""
        blob_name = f"{job_id}_{suffix}.json"
        
        if USE_ADAPTERS:
            storage = get_storage_adapter(self.storage_conn_str)
            storage.ensure_container(self.blob_container_results)
            data = json.dumps(result_data).encode('utf-8')
            storage.upload_blob(self.blob_container_results, blob_name, data, overwrite=True)
        else:
            blob_service_client = BlobServiceClient.from_connection_string(self.storage_conn_str)
            container_client = blob_service_client.get_container_client(self.blob_container_results)
            if not container_client.exists():
                container_client.create_container()
            
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(json.dumps(result_data), overwrite=True)
        
        return blob_name
    
    def check_step_status(self, job_id: str) -> str:
        """Check if step is already processed (idempotency check)"""
        try:
            blob_name = f"{job_id}_{self.step_name.lower()}.json"
            
            if USE_ADAPTERS:
                storage = get_storage_adapter(self.storage_conn_str)
                if storage.blob_exists(self.blob_container_results, blob_name):
                    return "COMPLETED"
            else:
                blob_service_client = BlobServiceClient.from_connection_string(self.storage_conn_str)
                blob_client = blob_service_client.get_blob_client(
                    container=self.blob_container_results,
                    blob=blob_name
                )
                if blob_client.exists():
                    return "COMPLETED"
        except:
            pass
        return "PENDING"
    
    async def send_success(self, sb_client, job_id: str, result: dict, metrics: StepMetrics):
        """Send success event to router with metrics"""
        result_msg = {
            "job_id": job_id,
            "event": "STEP_COMPLETED",
            "step_name": self.step_name,
            "result": result,
            "metrics": metrics.to_dict()
        }
        sender = sb_client.get_queue_sender(self.router_queue)
        await sender.send_messages(ServiceBusMessage(json.dumps(result_msg)))
    
    async def send_failure(self, sb_client, job_id: str, error: str, metrics: StepMetrics):
        """Send failure event to router with metrics"""
        metrics.error_message = error
        fail_msg = {
            "job_id": job_id,
            "event": "STEP_FAILED",
            "step_name": self.step_name,
            "error": error,
            "metrics": metrics.to_dict()
        }
        sender = sb_client.get_queue_sender(self.router_queue)
        await sender.send_messages(ServiceBusMessage(json.dumps(fail_msg)))
    
    @abstractmethod
    async def process(self, job_id: str, payload: dict, metrics: StepMetrics, sb_client) -> dict:
        """
        Process the job. Must be implemented by subclasses.
        
        Args:
            job_id: Unique job identifier
            payload: Message payload from queue
            metrics: StepMetrics object to populate with processing metrics
            sb_client: Service Bus client for sending messages
            
        Returns: result dict to be sent to router
        Raises: Exception on failure (include error_code in metrics before raising)
        """
        pass
    
    async def handle_message(self, msg, sb_client):
        """Handle incoming message with metrics collection"""
        body = json.loads(str(msg))
        job_id = body.get("job_id")
        
        # Initialize metrics
        metrics = StepMetrics(
            worker_id=self.worker_id,
            worker_node=self.worker_node,
            worker_node_pool=self.worker_node_pool,
            dequeued_at=self._now_utc()
        )
        
        # Extract queued_at from message if available
        if "queued_at" in body:
            try:
                metrics.queued_at = datetime.fromisoformat(body["queued_at"])
            except:
                pass
        
        # Calculate queue wait time
        if metrics.queued_at and metrics.dequeued_at:
            delta = metrics.dequeued_at - metrics.queued_at
            metrics.queue_wait_ms = int(delta.total_seconds() * 1000)
        
        print(f"[{self.step_name}] Processing Job {job_id} (queue wait: {metrics.queue_wait_ms}ms)")
        
        # Idempotency check
        status = self.check_step_status(job_id)
        if status == "COMPLETED":
            print(f"[{self.step_name}] Job {job_id} already processed. Skipping.")
            return
        
        # Start processing
        metrics.started_at = self._now_utc()
        start_time = time.perf_counter()
        
        try:
            result = await self.process(job_id, body, metrics, sb_client)
            
            # Record completion time
            metrics.completed_at = self._now_utc()
            metrics.processing_duration_ms = int((time.perf_counter() - start_time) * 1000)
            
            print(f"[{self.step_name}] Job {job_id} completed in {metrics.processing_duration_ms}ms")
            await self.send_success(sb_client, job_id, result, metrics)
            
        except Exception as e:
            metrics.completed_at = self._now_utc()
            metrics.processing_duration_ms = int((time.perf_counter() - start_time) * 1000)
            
            # Set error code if not already set by subclass
            if not metrics.error_code:
                metrics.error_code = type(e).__name__
            
            print(f"[{self.step_name}] Error: {e}")
            await self.send_failure(sb_client, job_id, str(e), metrics)
    
    async def run(self):
        """Main worker loop"""
        print(f"[{self.step_name}] Worker starting on queue: {self.queue_name}")
        print(f"[{self.step_name}] Worker ID: {self.worker_id}, Node: {self.worker_node}, Pool: {self.worker_node_pool}")
        
        if USE_ADAPTERS:
            async with get_message_broker(self.servicebus_conn_str) as client:
                receiver = await client.get_queue_receiver(queue_name=self.queue_name)
                async with receiver:
                    while self.running:
                        try:
                            # Use receive with timeout to allow checking self.running
                            messages = await receiver.receive_messages(max_message_count=1, max_wait_time=5)
                            for msg in messages:
                                await self.handle_message(msg, client)
                                await receiver.complete_message(msg)
                        except Exception as e:
                            print(f"[{self.step_name}] Loop error: {e}")
                            await asyncio.sleep(1)
        else:
            async with ServiceBusClient.from_connection_string(self.servicebus_conn_str) as client:
                receiver = client.get_queue_receiver(queue_name=self.queue_name)
                async with receiver:
                    while self.running:
                        try:
                            # Use receive with timeout to allow checking self.running
                            messages = await receiver.receive_messages(max_message_count=1, max_wait_time=5)
                            for msg in messages:
                                await self.handle_message(msg, client)
                                await receiver.complete_message(msg)
                        except Exception as e:
                            print(f"[{self.step_name}] Loop error: {e}")
                            await asyncio.sleep(1)
        
        print(f"[{self.step_name}] Worker shutdown complete.")
