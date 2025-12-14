import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
from sqlalchemy import create_engine, text
from azure.servicebus.management import ServiceBusAdministrationClient

# Add parent directory to path to import database/models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

# Config
st.set_page_config(page_title="Speech Flow Ops", layout="wide")
st.title("🎙️ Speech Flow Operations Dashboard")

# Database Connection
@st.cache_resource
def get_db_engine():
    return create_engine(settings.DATABASE_URL)

# Service Bus Client
@st.cache_resource
def get_sb_admin_client():
    return ServiceBusAdministrationClient.from_connection_string(settings.SERVICEBUS_CONNECTION_STRING)


def get_queue_depths():
    """Get current queue depths from Service Bus"""
    try:
        client = get_sb_admin_client()
        queues = ["lid-jobs", "whisper-jobs", "azure-ai-jobs", "job-events"]
        data = []
        for q in queues:
            props = client.get_queue_runtime_properties(q)
            data.append({
                "Queue": q,
                "Active": props.active_message_count,
                "Dead Letter": props.dead_letter_message_count
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching queue stats: {e}")
        return pd.DataFrame()


def get_job_stats():
    """Get job statistics for the last 24 hours"""
    engine = get_db_engine()
    query = """
    SELECT 
        status,
        COUNT(*) as count,
        COALESCE(SUM(audio_duration_seconds), 0) as total_audio_seconds,
        COALESCE(SUM(total_tokens_used), 0) as total_tokens,
        COALESCE(SUM(total_cost_usd), 0) as total_cost
    FROM jobs 
    WHERE created_at > NOW() - INTERVAL '24 hours'
    GROUP BY status
    """
    return pd.read_sql(query, engine)


def get_hourly_throughput():
    """Get hourly job throughput for the last 24 hours"""
    engine = get_db_engine()
    query = """
    SELECT 
        date_trunc('hour', created_at) as hour,
        COUNT(*) as job_count,
        COALESCE(SUM(audio_duration_seconds), 0) as audio_seconds,
        AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_duration_seconds
    FROM jobs 
    WHERE created_at > NOW() - INTERVAL '24 hours'
    GROUP BY date_trunc('hour', created_at)
    ORDER BY hour
    """
    return pd.read_sql(query, engine)


def get_step_performance():
    """Get step-level performance metrics"""
    engine = get_db_engine()
    query = """
    SELECT 
        step_name,
        worker_node_pool,
        COUNT(*) as count,
        AVG(queue_wait_ms) as avg_queue_wait_ms,
        AVG(processing_duration_ms) as avg_processing_ms,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_duration_ms) as p95_processing_ms,
        AVG(transcription_rtf) as avg_rtf,
        SUM(total_tokens) as total_tokens,
        SUM(api_cost_usd) as total_cost
    FROM job_steps
    WHERE queued_at > NOW() - INTERVAL '24 hours'
    GROUP BY step_name, worker_node_pool
    ORDER BY step_name
    """
    return pd.read_sql(query, engine)


def get_error_breakdown():
    """Get error breakdown for the last 7 days"""
    engine = get_db_engine()
    query = """
    SELECT 
        step_name,
        error_code,
        COUNT(*) as error_count,
        AVG(retry_count) as avg_retries
    FROM job_steps js
    JOIN jobs j ON js.job_id = j.job_id
    WHERE js.status = 'FAILED'
      AND j.created_at > NOW() - INTERVAL '7 days'
    GROUP BY step_name, error_code
    ORDER BY error_count DESC
    LIMIT 10
    """
    return pd.read_sql(query, engine)


def get_language_distribution():
    """Get language distribution for processed jobs"""
    engine = get_db_engine()
    query = """
    SELECT 
        COALESCE(source_language, 'unknown') as language,
        COUNT(*) as count,
        SUM(audio_duration_seconds) as audio_seconds
    FROM jobs 
    WHERE created_at > NOW() - INTERVAL '7 days'
      AND status = 'COMPLETED'
    GROUP BY source_language
    ORDER BY count DESC
    """
    return pd.read_sql(query, engine)


def get_daily_trends():
    """Get daily metrics from aggregated table"""
    engine = get_db_engine()
    query = """
    SELECT 
        metric_date,
        total_jobs,
        completed_jobs,
        failed_jobs,
        total_audio_seconds,
        total_cost_usd,
        p50_job_duration_ms,
        p95_job_duration_ms,
        avg_transcription_rtf
    FROM daily_metrics
    WHERE metric_date > CURRENT_DATE - INTERVAL '30 days'
    ORDER BY metric_date
    """
    try:
        return pd.read_sql(query, engine)
    except:
        return pd.DataFrame()


def get_recent_jobs():
    """Get most recent jobs with key metrics"""
    engine = get_db_engine()
    query = """
    SELECT 
        job_id, 
        workflow_type,
        status, 
        source_language,
        audio_duration_seconds,
        total_tokens_used,
        total_cost_usd,
        created_at,
        EXTRACT(EPOCH FROM (completed_at - created_at)) as duration_seconds
    FROM jobs 
    ORDER BY created_at DESC 
    LIMIT 20
    """
    return pd.read_sql(query, engine)


# =============================================================================
# DASHBOARD LAYOUT
# =============================================================================

# Sidebar
st.sidebar.header("⚙️ Controls")
auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
if st.sidebar.button("🔄 Refresh Now"):
    st.rerun()

# Date filter
st.sidebar.header("📅 Date Range")
date_range = st.sidebar.selectbox(
    "Select Range",
    ["Last 24 Hours", "Last 7 Days", "Last 30 Days"],
    index=0
)

# =============================================================================
# KEY METRICS ROW
# =============================================================================
st.header("📊 Key Metrics (Last 24 Hours)")

job_stats = get_job_stats()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_jobs = job_stats['count'].sum() if not job_stats.empty else 0
    st.metric("Total Jobs", f"{total_jobs:,}")

with col2:
    completed = job_stats[job_stats['status'] == 'COMPLETED']['count'].sum() if not job_stats.empty else 0
    st.metric("Completed", f"{completed:,}", delta=f"{(completed/total_jobs*100):.1f}%" if total_jobs > 0 else "0%")

with col3:
    failed = job_stats[job_stats['status'] == 'FAILED']['count'].sum() if not job_stats.empty else 0
    st.metric("Failed", f"{failed:,}", delta=f"-{(failed/total_jobs*100):.1f}%" if total_jobs > 0 else "0%", delta_color="inverse")

with col4:
    total_audio = job_stats['total_audio_seconds'].sum() if not job_stats.empty else 0
    st.metric("Audio Processed", f"{total_audio/3600:.1f} hrs")

with col5:
    total_cost = float(job_stats['total_cost'].sum()) if not job_stats.empty else 0
    st.metric("API Cost", f"${total_cost:.2f}")

# =============================================================================
# CHARTS ROW 1: Throughput & Queue Status
# =============================================================================
st.header("📈 Real-Time Monitoring")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Hourly Throughput")
    hourly_df = get_hourly_throughput()
    if not hourly_df.empty:
        fig = px.bar(
            hourly_df, 
            x='hour', 
            y='job_count',
            labels={'hour': 'Hour', 'job_count': 'Jobs'},
            color_discrete_sequence=['#1f77b4']
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available")

with col2:
    st.subheader("Queue Depths")
    queue_df = get_queue_depths()
    if not queue_df.empty:
        fig = px.bar(
            queue_df, 
            x='Queue', 
            y=['Active', 'Dead Letter'],
            barmode='group',
            color_discrete_sequence=['#2ecc71', '#e74c3c']
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No queue data available")

# =============================================================================
# CHARTS ROW 2: Step Performance & Errors
# =============================================================================
st.header("⚡ Performance Analysis")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Step Processing Times (ms)")
    step_df = get_step_performance()
    if not step_df.empty:
        fig = go.Figure()
        for step in step_df['step_name'].unique():
            step_data = step_df[step_df['step_name'] == step]
            fig.add_trace(go.Bar(
                name=step,
                x=['Avg', 'P95'],
                y=[step_data['avg_processing_ms'].values[0], step_data['p95_processing_ms'].values[0]]
            ))
        fig.update_layout(barmode='group', height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Show detailed table
        st.dataframe(
            step_df[['step_name', 'count', 'avg_queue_wait_ms', 'avg_processing_ms', 'avg_rtf', 'total_tokens']].round(2),
            hide_index=True
        )
    else:
        st.info("No step data available")

with col2:
    st.subheader("Error Breakdown (Last 7 Days)")
    error_df = get_error_breakdown()
    if not error_df.empty:
        fig = px.bar(
            error_df, 
            x='error_count', 
            y='step_name',
            color='error_code',
            orientation='h',
            labels={'error_count': 'Count', 'step_name': 'Step'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("No errors in the last 7 days! 🎉")

# =============================================================================
# CHARTS ROW 3: Language & Cost
# =============================================================================
st.header("🌍 Language & Cost Analysis")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Language Distribution")
    lang_df = get_language_distribution()
    if not lang_df.empty:
        fig = px.pie(
            lang_df, 
            values='count', 
            names='language',
            hole=0.4
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No language data available")

with col2:
    st.subheader("Daily Cost Trend")
    daily_df = get_daily_trends()
    if not daily_df.empty:
        fig = px.line(
            daily_df, 
            x='metric_date', 
            y='total_cost_usd',
            labels={'metric_date': 'Date', 'total_cost_usd': 'Cost ($)'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Run daily aggregation job to see trends")

# =============================================================================
# RECENT JOBS TABLE
# =============================================================================
st.header("📋 Recent Jobs")

jobs_df = get_recent_jobs()
if not jobs_df.empty:
    # Format the dataframe for display
    jobs_df['duration_seconds'] = jobs_df['duration_seconds'].round(1)
    jobs_df['total_cost_usd'] = jobs_df['total_cost_usd'].apply(lambda x: f"${float(x):.4f}" if x else "-")
    jobs_df['audio_duration_seconds'] = jobs_df['audio_duration_seconds'].apply(lambda x: f"{float(x):.1f}s" if x else "-")
    
    # Add status emoji
    status_emoji = {
        'COMPLETED': '✅',
        'FAILED': '❌',
        'PROCESSING': '🔄',
        'PENDING': '⏳',
        'QUEUED': '📥'
    }
    jobs_df['status'] = jobs_df['status'].apply(lambda x: f"{status_emoji.get(x, '')} {x}")
    
    st.dataframe(
        jobs_df[[
            'job_id', 'workflow_type', 'status', 'source_language',
            'audio_duration_seconds', 'duration_seconds', 'total_tokens_used', 
            'total_cost_usd', 'created_at'
        ]],
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("No jobs found")

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Auto-refresh
if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()
