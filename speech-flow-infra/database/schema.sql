-- ============================================================
-- JOBS TABLE
-- ============================================================
CREATE TABLE jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- PENDING, PROCESSING, COMPLETED, FAILED
    workflow_type VARCHAR(50) NOT NULL, -- e.g., 'transcribe_only', 'full_pipeline'
    
    -- Audio file metadata (for throughput analysis)
    audio_filename VARCHAR(255) NOT NULL,
    audio_duration_seconds NUMERIC(10, 2),  -- Duration of audio file
    audio_file_size_bytes BIGINT,           -- File size for bandwidth analysis
    audio_format VARCHAR(20),               -- wav, mp3, m4a, etc.
    audio_sample_rate INTEGER,              -- 16000, 44100, etc.
    audio_channels INTEGER,                 -- 1=mono, 2=stereo
    
    -- Language tracking
    source_language VARCHAR(10),            -- Detected or specified
    target_language VARCHAR(10) DEFAULT 'en',
    
    -- Callback configuration
    callback_url TEXT,
    callback_sent_at TIMESTAMP WITH TIME ZONE,
    callback_status VARCHAR(20),            -- success, failed, pending
    
    -- Priority and SLA
    priority INTEGER DEFAULT 5,             -- 1=highest, 10=lowest
    sla_deadline TIMESTAMP WITH TIME ZONE,  -- Expected completion time
    
    -- Timing metrics
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    queued_at TIMESTAMP WITH TIME ZONE,     -- When job entered processing queue
    started_at TIMESTAMP WITH TIME ZONE,    -- When first step started
    completed_at TIMESTAMP WITH TIME ZONE,  -- When job finished (success or fail)
    
    -- Cost tracking (aggregated from steps)
    total_tokens_used INTEGER DEFAULT 0,
    total_cost_usd NUMERIC(10, 6) DEFAULT 0,
    
    -- Extensible metadata
    metadata JSONB -- Stores arbitrary job config
);

-- ============================================================
-- JOB STEPS TABLE
-- ============================================================
CREATE TABLE job_steps (
    step_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(job_id) ON DELETE CASCADE,
    step_name VARCHAR(50) NOT NULL, -- 'LID', 'TRANSCRIBE', 'TRANSLATE', 'SUMMARIZE'
    status VARCHAR(20) NOT NULL, -- QUEUED, IN_PROGRESS, SUCCESS, FAILED
    
    -- Worker identification (for capacity analysis)
    worker_id VARCHAR(100),             -- Pod name that processed it
    worker_node VARCHAR(100),           -- Kubernetes node name
    worker_node_pool VARCHAR(50),       -- 'default', 'gpu', etc.
    
    -- Queue metrics (for latency analysis)
    queued_at TIMESTAMP WITH TIME ZONE,     -- When message sent to queue
    dequeued_at TIMESTAMP WITH TIME ZONE,   -- When worker picked up message
    started_at TIMESTAMP WITH TIME ZONE,    -- When processing began
    completed_at TIMESTAMP WITH TIME ZONE,  -- When processing finished
    
    -- Derived durations (computed for easy querying)
    queue_wait_ms INTEGER,              -- dequeued_at - queued_at
    processing_duration_ms INTEGER,     -- completed_at - started_at
    
    -- Model/service information (for quality correlation)
    model_name VARCHAR(100),            -- 'facebook/mms-lid-126', 'large-v3', 'gpt-4.1'
    model_version VARCHAR(50),          -- Specific version for reproducibility
    
    -- LID-specific metrics
    detected_language VARCHAR(10),
    language_confidence NUMERIC(5, 4),  -- 0.0000 to 1.0000
    
    -- Transcription-specific metrics
    transcript_word_count INTEGER,
    transcript_char_count INTEGER,
    transcription_rtf NUMERIC(6, 3),    -- Real-time factor (processing_time / audio_duration)
    
    -- Azure OpenAI metrics (for cost tracking)
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    api_cost_usd NUMERIC(10, 6),        -- Calculated cost for this step
    
    -- Error tracking
    error_message TEXT,
    error_code VARCHAR(50),             -- Categorized error (TIMEOUT, MODEL_ERROR, etc.)
    retry_count INTEGER DEFAULT 0,
    
    -- Result storage
    result_blob_path TEXT,              -- Path to result in blob storage
    result_payload JSONB                -- Inline results for small payloads
);

-- ============================================================
-- WORKER METRICS TABLE (for capacity planning)
-- ============================================================
CREATE TABLE worker_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id VARCHAR(100) NOT NULL,
    worker_node VARCHAR(100),
    worker_node_pool VARCHAR(50),
    step_name VARCHAR(50) NOT NULL,
    
    -- Snapshot time
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Resource utilization
    cpu_percent NUMERIC(5, 2),
    memory_mb INTEGER,
    gpu_percent NUMERIC(5, 2),
    gpu_memory_mb INTEGER,
    
    -- Throughput metrics
    jobs_processed_last_hour INTEGER,
    avg_processing_ms_last_hour INTEGER,
    error_rate_last_hour NUMERIC(5, 4)
);

-- ============================================================
-- DAILY AGGREGATES TABLE (for historical trending)
-- ============================================================
CREATE TABLE daily_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_date DATE NOT NULL,
    
    -- Job volume metrics
    total_jobs INTEGER DEFAULT 0,
    completed_jobs INTEGER DEFAULT 0,
    failed_jobs INTEGER DEFAULT 0,
    
    -- Audio volume
    total_audio_seconds NUMERIC(12, 2) DEFAULT 0,
    total_audio_bytes BIGINT DEFAULT 0,
    
    -- Timing percentiles (in milliseconds)
    p50_job_duration_ms INTEGER,
    p95_job_duration_ms INTEGER,
    p99_job_duration_ms INTEGER,
    p50_queue_wait_ms INTEGER,
    p95_queue_wait_ms INTEGER,
    
    -- Cost metrics
    total_tokens_used BIGINT DEFAULT 0,
    total_cost_usd NUMERIC(12, 4) DEFAULT 0,
    
    -- Quality metrics
    avg_transcription_rtf NUMERIC(6, 3),
    avg_lid_confidence NUMERIC(5, 4),
    
    -- Breakdown by workflow type (JSONB for flexibility)
    metrics_by_workflow JSONB,
    -- Example: {"full_pipeline": {"count": 100, "avg_duration_ms": 5000}, ...}
    
    -- Breakdown by language
    metrics_by_language JSONB,
    -- Example: {"en": {"count": 80}, "zh": {"count": 15}, ...}
    
    UNIQUE(metric_date)
);

-- ============================================================
-- INDEXES
-- ============================================================

-- Jobs indexes
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at);
CREATE INDEX idx_jobs_customer_id ON jobs(customer_id);
CREATE INDEX idx_jobs_workflow_type ON jobs(workflow_type);
CREATE INDEX idx_jobs_source_language ON jobs(source_language);

-- Job steps indexes
CREATE INDEX idx_job_steps_job_id ON job_steps(job_id);
CREATE INDEX idx_job_steps_status ON job_steps(status);
CREATE INDEX idx_job_steps_step_name ON job_steps(step_name);
CREATE INDEX idx_job_steps_worker_id ON job_steps(worker_id);
CREATE INDEX idx_job_steps_queued_at ON job_steps(queued_at);

-- Worker metrics indexes
CREATE INDEX idx_worker_metrics_worker_id ON worker_metrics(worker_id);
CREATE INDEX idx_worker_metrics_recorded_at ON worker_metrics(recorded_at);

-- Daily metrics index
CREATE INDEX idx_daily_metrics_date ON daily_metrics(metric_date);

-- ============================================================
-- USEFUL VIEWS FOR PERFORMANCE ANALYSIS
-- ============================================================

-- View: Real-time job throughput
CREATE VIEW v_job_throughput AS
SELECT 
    date_trunc('hour', created_at) as hour,
    workflow_type,
    COUNT(*) as job_count,
    SUM(audio_duration_seconds) as total_audio_seconds,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) * 1000)::INTEGER as avg_duration_ms,
    SUM(total_cost_usd) as total_cost
FROM jobs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY date_trunc('hour', created_at), workflow_type
ORDER BY hour DESC;

-- View: Step performance by worker node pool
CREATE VIEW v_step_performance AS
SELECT 
    step_name,
    worker_node_pool,
    COUNT(*) as step_count,
    AVG(queue_wait_ms) as avg_queue_wait_ms,
    AVG(processing_duration_ms) as avg_processing_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_duration_ms) as p95_processing_ms,
    AVG(transcription_rtf) as avg_rtf,
    SUM(total_tokens) as total_tokens,
    SUM(api_cost_usd) as total_cost
FROM job_steps
WHERE queued_at > NOW() - INTERVAL '24 hours'
GROUP BY step_name, worker_node_pool;

-- View: Error analysis
CREATE VIEW v_error_analysis AS
SELECT 
    step_name,
    error_code,
    COUNT(*) as error_count,
    AVG(retry_count) as avg_retries,
    MAX(created_at) as last_occurrence
FROM job_steps js
JOIN jobs j ON js.job_id = j.job_id
WHERE js.status = 'FAILED'
  AND j.created_at > NOW() - INTERVAL '7 days'
GROUP BY step_name, error_code
ORDER BY error_count DESC;
