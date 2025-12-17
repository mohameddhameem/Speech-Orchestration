"""
Daily Metrics Aggregation Job

This script aggregates job and step metrics into the daily_metrics table
for historical trending and reporting. Typically runs as a Kubernetes CronJob
at midnight UTC.

Usage:
    python -m aggregation.daily_metrics_job

Schedule as CronJob:
    0 0 * * * (midnight UTC daily)
"""

import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import DailyMetrics, Job, JobStep
from sqlalchemy import case, func
from sqlalchemy.orm import Session


def get_percentile(values: list, percentile: float) -> Optional[int]:
    """Calculate percentile from a list of values"""
    if not values:
        return None
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile)
    return sorted_values[min(index, len(sorted_values) - 1)]


def aggregate_daily_metrics(db: Session, target_date: date) -> DailyMetrics:
    """
    Aggregate all metrics for a specific date.
    """
    print(f"Aggregating metrics for {target_date}")

    # Date range for the target day (UTC)
    start_time = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_time = start_time + timedelta(days=1)

    # Query jobs for this date
    jobs = db.query(Job).filter(Job.created_at >= start_time, Job.created_at < end_time).all()

    if not jobs:
        print(f"No jobs found for {target_date}")
        return None

    # Basic job counts
    total_jobs = len(jobs)
    completed_jobs = sum(1 for j in jobs if j.status == "COMPLETED")
    failed_jobs = sum(1 for j in jobs if j.status == "FAILED")

    # Audio metrics
    total_audio_seconds = sum(float(j.audio_duration_seconds or 0) for j in jobs)
    total_audio_bytes = sum(j.audio_file_size_bytes or 0 for j in jobs)

    # Cost metrics
    total_tokens = sum(j.total_tokens_used or 0 for j in jobs)
    total_cost = sum(float(j.total_cost_usd or 0) for j in jobs)

    # Job duration calculations (for completed jobs only)
    job_durations_ms = []
    for job in jobs:
        if job.completed_at and job.created_at:
            duration = (job.completed_at - job.created_at).total_seconds() * 1000
            job_durations_ms.append(int(duration))

    # Query steps for queue wait times
    steps = db.query(JobStep).filter(JobStep.queued_at >= start_time, JobStep.queued_at < end_time).all()

    queue_wait_times = [s.queue_wait_ms for s in steps if s.queue_wait_ms is not None]

    # Transcription RTF (only from TRANSCRIBE steps)
    transcription_rtfs = [
        float(s.transcription_rtf) for s in steps if s.step_name == "TRANSCRIBE" and s.transcription_rtf is not None
    ]

    # LID confidence (only from LID steps)
    lid_confidences = [
        float(s.language_confidence) for s in steps if s.step_name == "LID" and s.language_confidence is not None
    ]

    # Breakdown by workflow type
    workflow_breakdown = {}
    for workflow_type in set(j.workflow_type for j in jobs):
        wf_jobs = [j for j in jobs if j.workflow_type == workflow_type]
        wf_durations = []
        for j in wf_jobs:
            if j.completed_at and j.created_at:
                wf_durations.append(int((j.completed_at - j.created_at).total_seconds() * 1000))

        workflow_breakdown[workflow_type] = {
            "count": len(wf_jobs),
            "completed": sum(1 for j in wf_jobs if j.status == "COMPLETED"),
            "failed": sum(1 for j in wf_jobs if j.status == "FAILED"),
            "avg_duration_ms": int(sum(wf_durations) / len(wf_durations)) if wf_durations else None,
            "total_tokens": sum(j.total_tokens_used or 0 for j in wf_jobs),
            "total_cost_usd": round(sum(float(j.total_cost_usd or 0) for j in wf_jobs), 4),
        }

    # Breakdown by language
    language_breakdown = {}
    for job in jobs:
        lang = job.source_language or "unknown"
        if lang not in language_breakdown:
            language_breakdown[lang] = {"count": 0, "audio_seconds": 0}
        language_breakdown[lang]["count"] += 1
        language_breakdown[lang]["audio_seconds"] += float(job.audio_duration_seconds or 0)

    # Create or update DailyMetrics record
    existing = db.query(DailyMetrics).filter(DailyMetrics.metric_date == target_date).first()

    if existing:
        metrics = existing
    else:
        metrics = DailyMetrics(metric_date=target_date)
        db.add(metrics)

    # Populate metrics
    metrics.total_jobs = total_jobs
    metrics.completed_jobs = completed_jobs
    metrics.failed_jobs = failed_jobs
    metrics.total_audio_seconds = Decimal(str(round(total_audio_seconds, 2)))
    metrics.total_audio_bytes = total_audio_bytes
    metrics.total_tokens_used = total_tokens
    metrics.total_cost_usd = Decimal(str(round(total_cost, 4)))

    # Duration percentiles
    metrics.p50_job_duration_ms = get_percentile(job_durations_ms, 0.50)
    metrics.p95_job_duration_ms = get_percentile(job_durations_ms, 0.95)
    metrics.p99_job_duration_ms = get_percentile(job_durations_ms, 0.99)

    # Queue wait percentiles
    metrics.p50_queue_wait_ms = get_percentile(queue_wait_times, 0.50)
    metrics.p95_queue_wait_ms = get_percentile(queue_wait_times, 0.95)

    # Quality metrics
    metrics.avg_transcription_rtf = (
        Decimal(str(round(sum(transcription_rtfs) / len(transcription_rtfs), 3))) if transcription_rtfs else None
    )
    metrics.avg_lid_confidence = (
        Decimal(str(round(sum(lid_confidences) / len(lid_confidences), 4))) if lid_confidences else None
    )

    # JSONB breakdowns
    metrics.metrics_by_workflow = workflow_breakdown
    metrics.metrics_by_language = language_breakdown

    db.commit()

    print(f"Aggregated: {total_jobs} jobs, {completed_jobs} completed, {failed_jobs} failed")
    print(f"Audio: {total_audio_seconds:.1f}s, Tokens: {total_tokens}, Cost: ${total_cost:.4f}")

    return metrics


def run_aggregation(days_back: int = 1):
    """
    Run aggregation for the specified number of days back.
    Default is 1 (yesterday).
    """
    db = SessionLocal()
    try:
        for i in range(days_back, 0, -1):
            target_date = date.today() - timedelta(days=i)
            aggregate_daily_metrics(db, target_date)
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aggregate daily metrics")
    parser.add_argument(
        "--days-back", type=int, default=1, help="Number of days to aggregate (default: 1 for yesterday)"
    )
    parser.add_argument("--date", type=str, help="Specific date to aggregate (YYYY-MM-DD format)")

    args = parser.parse_args()

    if args.date:
        target_date = date.fromisoformat(args.date)
        db = SessionLocal()
        try:
            aggregate_daily_metrics(db, target_date)
        finally:
            db.close()
    else:
        run_aggregation(args.days_back)

    print("Aggregation complete.")
