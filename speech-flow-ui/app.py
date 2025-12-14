"""
Simple UI for Speech Flow - Audio Upload and Results Download

This is a basic Streamlit app that allows users to:
1. Upload audio files
2. Submit jobs to the Speech Flow API
3. Monitor job status
4. Download results in CSV/Excel format

All business logic is handled by the API - this is just a UI wrapper.
"""

import io
import os
from typing import Any, Dict, Optional

import pandas as pd
import requests
import streamlit as st

# Configuration - API endpoint
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(page_title="Speech Flow - Upload & Process", page_icon="🎤", layout="centered")

st.title("🎤 Speech Flow - Audio Processing")
st.markdown("Upload audio files and download processed results")

# Initialize session state
if "job_id" not in st.session_state:
    st.session_state.job_id = None
if "job_status" not in st.session_state:
    st.session_state.job_status = None
if "upload_url" not in st.session_state:
    st.session_state.upload_url = None
if "results_data" not in st.session_state:
    st.session_state.results_data = None


def submit_job(
    audio_filename: str, workflow_type: str, source_language: Optional[str], target_language: str
) -> Dict[str, Any]:
    """Submit a new job to the API"""
    payload = {"audio_filename": audio_filename, "workflow_type": workflow_type, "target_language": target_language}

    if source_language:
        payload["source_language"] = source_language

    response = requests.post(f"{API_BASE_URL}/jobs", json=payload)
    response.raise_for_status()
    return response.json()


def upload_audio_file(upload_url: str, audio_file) -> bool:
    """Upload audio file to the provided SAS URL"""
    try:
        # For blob storage, we need to use PUT request
        headers = {"x-ms-blob-type": "BlockBlob"}
        response = requests.put(upload_url, data=audio_file.getvalue(), headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Upload failed: {str(e)}")
        return False


def start_job(job_id: str) -> Dict[str, Any]:
    """Start processing a job after upload"""
    response = requests.post(f"{API_BASE_URL}/jobs/{job_id}/start")
    response.raise_for_status()
    return response.json()


def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get current status of a job"""
    response = requests.get(f"{API_BASE_URL}/jobs/{job_id}")
    response.raise_for_status()
    return response.json()


def get_job_results(job_id: str) -> Dict[str, Any]:
    """Get results of a completed job"""
    response = requests.get(f"{API_BASE_URL}/jobs/{job_id}/results")
    response.raise_for_status()
    return response.json()


def format_results_as_dataframe(results: Dict[str, Any]) -> pd.DataFrame:
    """Convert job results to a pandas DataFrame for download"""
    rows = []

    # Basic job info
    row = {
        "Job ID": results.get("job_id"),
        "Status": results.get("status"),
        "Workflow Type": results.get("workflow_type"),
        "Audio Filename": results.get("audio_filename"),
        "Detected Language": results.get("detected_language", "N/A"),
    }

    # Transcription
    if results.get("transcription"):
        trans = results["transcription"]
        row["Transcription Language"] = trans.get("language", "N/A")
        row["Transcription Text"] = trans.get("text", "N/A")
    else:
        row["Transcription Language"] = "N/A"
        row["Transcription Text"] = "N/A"

    # Translation
    if results.get("translation"):
        transl = results["translation"]
        row["Translation Source"] = transl.get("source_language", "N/A")
        row["Translation Target"] = transl.get("target_language", "N/A")
        row["Original Text"] = transl.get("original_text", "N/A")
        row["Translated Text"] = transl.get("translated_text", "N/A")
    else:
        row["Translation Source"] = "N/A"
        row["Translation Target"] = "N/A"
        row["Original Text"] = "N/A"
        row["Translated Text"] = "N/A"

    # Summary
    if results.get("summary"):
        summ = results["summary"]
        row["Summary"] = summ.get("summary", "N/A")
        key_points = summ.get("key_points")
        row["Key Points"] = ", ".join(key_points) if key_points else "N/A"
    else:
        row["Summary"] = "N/A"
        row["Key Points"] = "N/A"

    row["Completed At"] = results.get("completed_at", "N/A")

    rows.append(row)
    return pd.DataFrame(rows)


# ============== UI Layout ==============

# Workflow configuration
st.header("⚙️ Job Configuration")

col1, col2 = st.columns(2)

with col1:
    workflow_type = st.selectbox(
        "Workflow Type",
        ["full_pipeline", "transcribe_only", "lid_only", "translate_only", "summarize_only"],
        help="Select the processing workflow",
    )

with col2:
    target_language = st.selectbox(
        "Target Language", ["en", "es", "fr", "de", "zh", "ja", "ar"], help="Target language for translation"
    )

# Source language (conditional)
source_language = None
if workflow_type in ["transcribe_only", "translate_only", "summarize_only"]:
    source_language = st.text_input(
        "Source Language (required)", placeholder="e.g., en, zh, yue", help="Source language code for processing"
    )

st.divider()

# File upload
st.header("📁 Upload Audio File")

uploaded_file = st.file_uploader(
    "Choose an audio file", type=["wav", "mp3", "m4a", "ogg", "flac"], help="Upload your audio file for processing"
)

if uploaded_file is not None:
    st.success(f"File selected: {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)")

    # Submit button
    if st.button("🚀 Submit Job", type="primary"):
        # Validate source language if required
        if workflow_type in ["transcribe_only", "translate_only", "summarize_only"] and not source_language:
            st.error("Source language is required for this workflow type")
        else:
            try:
                with st.spinner("Submitting job..."):
                    # Step 1: Submit job
                    job_response = submit_job(
                        audio_filename=uploaded_file.name,
                        workflow_type=workflow_type,
                        source_language=source_language,
                        target_language=target_language,
                    )

                    st.session_state.job_id = job_response["job_id"]
                    st.session_state.upload_url = job_response["upload_url"]
                    st.session_state.job_status = job_response["status"]

                    st.success(f"Job created: {st.session_state.job_id}")

                with st.spinner("Uploading audio file..."):
                    # Step 2: Upload audio file
                    if upload_audio_file(st.session_state.upload_url, uploaded_file):
                        st.success("Audio file uploaded successfully")

                        # Step 3: Start job processing
                        start_response = start_job(st.session_state.job_id)
                        st.session_state.job_status = start_response["status"]
                        st.success("Job started! Processing...")
                        st.rerun()

            except requests.exceptions.RequestException as e:
                st.error(f"Error: {str(e)}")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")

st.divider()

# Job status monitoring
if st.session_state.job_id:
    st.header("📊 Job Status")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.info(f"**Job ID:** `{st.session_state.job_id}`")

    with col2:
        if st.button("🔄 Refresh Status"):
            st.rerun()

    try:
        # Get current status
        status_response = get_job_status(st.session_state.job_id)
        st.session_state.job_status = status_response["status"]

        # Display status
        status_map = {
            "pending_upload": ("⏳", "warning"),
            "queued": ("📥", "info"),
            "processing": ("🔄", "info"),
            "completed": ("✅", "success"),
            "partial_complete": ("⚠️", "warning"),
            "failed": ("❌", "error"),
            "cancelled": ("🚫", "warning"),
        }

        icon, status_type = status_map.get(st.session_state.job_status, ("❓", "info"))

        if status_type == "success":
            st.success(f"{icon} Status: **{st.session_state.job_status.upper()}**")
        elif status_type == "error":
            st.error(f"{icon} Status: **{st.session_state.job_status.upper()}**")
        elif status_type == "warning":
            st.warning(f"{icon} Status: **{st.session_state.job_status.upper()}**")
        else:
            st.info(f"{icon} Status: **{st.session_state.job_status.upper()}**")

        # Show steps
        if status_response.get("steps"):
            st.subheader("Processing Steps")
            steps_data = []
            for step in status_response["steps"]:
                steps_data.append(
                    {
                        "Step": step["step_type"],
                        "Status": step["status"],
                        "Started": step.get("started_at", "N/A"),
                        "Completed": step.get("completed_at", "N/A"),
                        "Retries": step.get("retry_count", 0),
                    }
                )

            st.dataframe(pd.DataFrame(steps_data), use_container_width=True, hide_index=True)

        # Auto-refresh for in-progress jobs
        if st.session_state.job_status in ["queued", "processing"]:
            st.info("🔄 Job is processing... Click 'Refresh Status' button above to update")

        # Download results for completed jobs
        if st.session_state.job_status in ["completed", "partial_complete"]:
            st.divider()
            st.header("📥 Download Results")

            if st.button("📊 Fetch Results", type="primary"):
                try:
                    with st.spinner("Fetching results..."):
                        results = get_job_results(st.session_state.job_id)
                        st.session_state.results_data = results
                        st.success("Results fetched successfully!")

                except requests.exceptions.RequestException as e:
                    st.error(f"Error fetching results: {str(e)}")

            # Display and download results
            if st.session_state.results_data:
                results_df = format_results_as_dataframe(st.session_state.results_data)

                st.subheader("Results Preview")
                st.dataframe(results_df, use_container_width=True, hide_index=True)

                # Download buttons
                col1, col2 = st.columns(2)

                with col1:
                    # CSV download
                    csv_buffer = io.StringIO()
                    results_df.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue()

                    st.download_button(
                        label="📄 Download as CSV",
                        data=csv_data,
                        file_name=f"speech_flow_results_{st.session_state.job_id}.csv",
                        mime="text/csv",
                    )

                with col2:
                    # Excel download
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                        results_df.to_excel(writer, index=False, sheet_name="Results")
                    excel_data = excel_buffer.getvalue()

                    st.download_button(
                        label="📊 Download as Excel",
                        data=excel_data,
                        file_name=f"speech_flow_results_{st.session_state.job_id}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

    except requests.exceptions.RequestException as e:
        st.error(f"Error checking job status: {str(e)}")

# Footer
st.divider()
st.caption(f"Speech Flow API: {API_BASE_URL}")

# Reset button
if st.session_state.job_id:
    if st.button("🔄 Start New Job"):
        st.session_state.job_id = None
        st.session_state.job_status = None
        st.session_state.upload_url = None
        st.session_state.results_data = None
        st.rerun()
