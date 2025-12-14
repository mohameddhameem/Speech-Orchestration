from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Numeric, BigInteger, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from database import Base


class Job(Base):
    """
    Main jobs table with comprehensive metadata for performance tracking.
    """
    __tablename__ = "jobs"

    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    workflow_type = Column(String(50), nullable=False)
    
    # Audio file metadata (for throughput analysis)
    audio_filename = Column(String(255), nullable=False)
    audio_duration_seconds = Column(Numeric(10, 2))  # Duration of audio file
    audio_file_size_bytes = Column(BigInteger)  # File size for bandwidth analysis
    audio_format = Column(String(20))  # wav, mp3, m4a, etc.
    audio_sample_rate = Column(Integer)  # 16000, 44100, etc.
    audio_channels = Column(Integer)  # 1=mono, 2=stereo
    
    # Language tracking
    source_language = Column(String(10))  # Detected or specified
    target_language = Column(String(10), default='en')
    
    # Callback configuration
    callback_url = Column(Text)
    callback_sent_at = Column(DateTime(timezone=True))
    callback_status = Column(String(20))  # success, failed, pending
    
    # Priority and SLA
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest
    sla_deadline = Column(DateTime(timezone=True))  # Expected completion time
    
    # Timing metrics
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    queued_at = Column(DateTime(timezone=True))  # When job entered processing queue
    started_at = Column(DateTime(timezone=True))  # When first step started
    completed_at = Column(DateTime(timezone=True))  # When job finished
    
    # Cost tracking (aggregated from steps)
    total_tokens_used = Column(Integer, default=0)
    total_cost_usd = Column(Numeric(10, 6), default=0)
    
    # Extensible metadata
    metadata_ = Column("metadata", JSONB)

    steps = relationship("JobStep", back_populates="job", cascade="all, delete-orphan")


class JobStep(Base):
    """
    Processing steps with detailed metrics for each stage.
    """
    __tablename__ = "job_steps"

    step_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"))
    step_name = Column(String(50), nullable=False)  # LID, TRANSCRIBE, TRANSLATE, SUMMARIZE
    status = Column(String(20), nullable=False, default="QUEUED")
    
    # Worker identification (for capacity analysis)
    worker_id = Column(String(100))  # Pod name
    worker_node = Column(String(100))  # Kubernetes node name
    worker_node_pool = Column(String(50))  # 'default', 'gpu', etc.
    
    # Queue metrics (for latency analysis)
    queued_at = Column(DateTime(timezone=True))  # When message sent to queue
    dequeued_at = Column(DateTime(timezone=True))  # When worker picked up message
    started_at = Column(DateTime(timezone=True))  # When processing began
    completed_at = Column(DateTime(timezone=True))  # When processing finished
    
    # Derived durations (computed for easy querying)
    queue_wait_ms = Column(Integer)  # dequeued_at - queued_at
    processing_duration_ms = Column(Integer)  # completed_at - started_at
    
    # Model/service information (for quality correlation)
    model_name = Column(String(100))  # 'facebook/mms-lid-126', 'large-v3', 'gpt-4.1'
    model_version = Column(String(50))  # Specific version for reproducibility
    
    # LID-specific metrics
    detected_language = Column(String(10))
    language_confidence = Column(Numeric(5, 4))  # 0.0000 to 1.0000
    
    # Transcription-specific metrics
    transcript_word_count = Column(Integer)
    transcript_char_count = Column(Integer)
    transcription_rtf = Column(Numeric(6, 3))  # Real-time factor
    
    # Azure OpenAI metrics (for cost tracking)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    api_cost_usd = Column(Numeric(10, 6))
    
    # Error tracking
    error_message = Column(Text)
    error_code = Column(String(50))  # Categorized error
    retry_count = Column(Integer, default=0)
    
    # Result storage
    result_blob_path = Column(Text)
    result_payload = Column(JSONB)

    job = relationship("Job", back_populates="steps")


class WorkerMetrics(Base):
    """
    Worker resource utilization snapshots for capacity planning.
    """
    __tablename__ = "worker_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(String(100), nullable=False)
    worker_node = Column(String(100))
    worker_node_pool = Column(String(50))
    step_name = Column(String(50), nullable=False)
    
    # Snapshot time
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Resource utilization
    cpu_percent = Column(Numeric(5, 2))
    memory_mb = Column(Integer)
    gpu_percent = Column(Numeric(5, 2))
    gpu_memory_mb = Column(Integer)
    
    # Throughput metrics
    jobs_processed_last_hour = Column(Integer)
    avg_processing_ms_last_hour = Column(Integer)
    error_rate_last_hour = Column(Numeric(5, 4))


class DailyMetrics(Base):
    """
    Pre-aggregated daily metrics for historical trending and reporting.
    """
    __tablename__ = "daily_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_date = Column(Date, nullable=False, unique=True)
    
    # Job volume metrics
    total_jobs = Column(Integer, default=0)
    completed_jobs = Column(Integer, default=0)
    failed_jobs = Column(Integer, default=0)
    
    # Audio volume
    total_audio_seconds = Column(Numeric(12, 2), default=0)
    total_audio_bytes = Column(BigInteger, default=0)
    
    # Timing percentiles (in milliseconds)
    p50_job_duration_ms = Column(Integer)
    p95_job_duration_ms = Column(Integer)
    p99_job_duration_ms = Column(Integer)
    p50_queue_wait_ms = Column(Integer)
    p95_queue_wait_ms = Column(Integer)
    
    # Cost metrics
    total_tokens_used = Column(BigInteger, default=0)
    total_cost_usd = Column(Numeric(12, 4), default=0)
    
    # Quality metrics
    avg_transcription_rtf = Column(Numeric(6, 3))
    avg_lid_confidence = Column(Numeric(5, 4))
    
    # Breakdown by workflow type and language (JSONB for flexibility)
    metrics_by_workflow = Column(JSONB)
    metrics_by_language = Column(JSONB)
