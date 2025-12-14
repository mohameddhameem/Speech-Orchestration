#!/usr/bin/env python3
"""
Comprehensive Integration Test for Speech-Flow Local Deployment

Tests the complete workflow:
1. Job creation via API
2. SAS URL generation for upload
3. Audio file upload to Azurite
4. Job start and processing
5. Status checking
6. Results retrieval (when available)
7. Job listing and filtering

Usage:
    python test_integration_local.py

Environment:
    - Requires all services running (API, Azurite, Postgres)
    - Run ./start-services.ps1 first
"""

import io
import json
import time
import wave
from datetime import datetime
from typing import Any, Dict, Optional

import requests

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_AUDIO_DURATION_SECONDS = 1
TEST_SAMPLE_RATE = 16000


class Colors:
    """ANSI color codes for terminal output"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(message: str):
    """Print a header message"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(message: str):
    """Print a success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print an error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print a warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print an info message"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def generate_test_audio() -> bytes:
    """Generate a minimal WAV file for testing"""
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(TEST_SAMPLE_RATE)

        # Generate silent audio
        num_samples = TEST_SAMPLE_RATE * TEST_AUDIO_DURATION_SECONDS
        silent_data = b"\x00\x00" * num_samples
        wav_file.writeframes(silent_data)

    buffer.seek(0)
    audio_bytes = buffer.read()
    print_info(f"Generated test audio: {len(audio_bytes)} bytes, {TEST_AUDIO_DURATION_SECONDS}s duration")
    return audio_bytes


def test_health_check() -> bool:
    """Test API health endpoint"""
    print_header("TEST 1: Health Check")

    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()

        data = response.json()
        if data.get("status") == "healthy":
            print_success(f"API is healthy: {data}")
            return True
        else:
            print_error(f"Unexpected health response: {data}")
            return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


def test_create_job(workflow_type: str = "transcribe_only", source_language: str = "en") -> Optional[Dict[str, Any]]:
    """Test job creation and SAS URL generation"""
    print_header(f"TEST 2: Create Job ({workflow_type})")

    payload = {
        "audio_filename": f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}.wav",
        "workflow_type": workflow_type,
        "source_language": source_language,
        "target_language": "en",
    }

    print_info(f"Request payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(f"{API_BASE_URL}/jobs", json=payload, timeout=10)
        response.raise_for_status()

        data = response.json()
        job_id = data.get("job_id")
        upload_url = data.get("upload_url")
        status = data.get("status")

        print_success(f"Job created successfully")
        print_info(f"Job ID: {job_id}")
        print_info(f"Status: {status}")
        print_info(f"Upload URL: {upload_url[:100]}...")

        if not upload_url:
            print_error("No upload URL returned")
            return None

        if "devstoreaccount1" in upload_url:
            print_success("SAS URL correctly points to Azurite (devstoreaccount1)")
        else:
            print_warning("SAS URL might not point to local Azurite")

        return {"job_id": job_id, "upload_url": upload_url, "status": status, "filename": payload["audio_filename"]}

    except requests.exceptions.HTTPError as e:
        print_error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print_error(f"Job creation failed: {e}")
        return None


def test_upload_audio(upload_url: str, audio_bytes: bytes) -> bool:
    """Test audio file upload via SAS URL"""
    print_header("TEST 3: Upload Audio File")

    print_info(f"Uploading {len(audio_bytes)} bytes to Azurite...")

    try:
        headers = {"x-ms-blob-type": "BlockBlob", "Content-Type": "audio/wav"}

        response = requests.put(upload_url, data=audio_bytes, headers=headers, timeout=30)

        if response.status_code in [200, 201]:
            print_success(f"Upload successful (HTTP {response.status_code})")
            return True
        else:
            print_error(f"Upload failed: HTTP {response.status_code}")
            print_error(f"Response: {response.text}")
            return False

    except Exception as e:
        print_error(f"Upload failed: {e}")
        return False


def test_start_job(job_id: str) -> bool:
    """Test starting a job after upload"""
    print_header("TEST 4: Start Job Processing")

    print_info(f"Starting job {job_id}...")

    try:
        response = requests.post(f"{API_BASE_URL}/jobs/{job_id}/start", timeout=10)
        response.raise_for_status()

        data = response.json()
        status = data.get("status")
        message = data.get("message")

        print_success(f"Job started successfully")
        print_info(f"Status: {status}")
        print_info(f"Message: {message}")

        return True

    except requests.exceptions.HTTPError as e:
        print_error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        print_error(f"Job start failed: {e}")
        return False


def test_get_job_status(job_id: str, expected_status: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Test retrieving job status"""
    print_header("TEST 5: Get Job Status")

    print_info(f"Fetching status for job {job_id}...")

    try:
        response = requests.get(f"{API_BASE_URL}/jobs/{job_id}", timeout=10)
        response.raise_for_status()

        data = response.json()
        status = data.get("status")
        workflow_type = data.get("workflow_type")
        steps = data.get("steps", [])

        print_success(f"Status retrieved successfully")
        print_info(f"Status: {status}")
        print_info(f"Workflow: {workflow_type}")
        print_info(f"Steps: {len(steps)} processing steps")

        for step in steps:
            step_type = step.get("step_type")
            step_status = step.get("status")
            error = step.get("error_message")
            print_info(f"  - {step_type}: {step_status}" + (f" (Error: {error})" if error else ""))

        if expected_status and status != expected_status:
            print_warning(f"Expected status '{expected_status}', got '{status}'")

        return data

    except requests.exceptions.HTTPError as e:
        print_error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print_error(f"Status check failed: {e}")
        return None


def test_list_jobs(status_filter: Optional[str] = None, limit: int = 10) -> bool:
    """Test listing jobs with optional filtering"""
    print_header("TEST 6: List Jobs")

    params = {"limit": limit}
    if status_filter:
        params["status"] = status_filter
        print_info(f"Filtering by status: {status_filter}")

    try:
        response = requests.get(f"{API_BASE_URL}/jobs", params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        total = data.get("total", 0)
        jobs = data.get("jobs", [])

        print_success(f"Retrieved {len(jobs)} jobs (total: {total})")

        for i, job in enumerate(jobs[:5], 1):  # Show first 5
            job_id = job.get("job_id")
            status = job.get("status")
            workflow = job.get("workflow_type")
            filename = job.get("audio_filename")
            print_info(f"  {i}. {job_id[:8]}... | {status} | {workflow} | {filename}")

        if len(jobs) > 5:
            print_info(f"  ... and {len(jobs) - 5} more jobs")

        return True

    except requests.exceptions.HTTPError as e:
        print_error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        print_error(f"List jobs failed: {e}")
        return False


def test_get_job_results(job_id: str) -> Optional[Dict[str, Any]]:
    """Test retrieving job results (for completed jobs)"""
    print_header("TEST 7: Get Job Results")

    print_info(f"Fetching results for job {job_id}...")

    try:
        response = requests.get(f"{API_BASE_URL}/jobs/{job_id}/results", timeout=10)

        if response.status_code == 400:
            # Expected if job is not completed yet
            error_data = response.json()
            print_warning(f"Results not available: {error_data.get('detail', 'Unknown')}")
            return None

        response.raise_for_status()

        data = response.json()
        status = data.get("status")
        transcription = data.get("transcription")
        translation = data.get("translation")
        summary = data.get("summary")
        detected_language = data.get("detected_language")

        print_success(f"Results retrieved successfully")
        print_info(f"Status: {status}")

        if detected_language:
            print_info(f"Detected Language: {detected_language}")

        if transcription:
            print_info(f"Transcription: {transcription.get('text', '')[:100]}...")

        if translation:
            print_info(f"Translation: {translation.get('translated_text', '')[:100]}...")

        if summary:
            print_info(f"Summary: {summary.get('summary', '')[:100]}...")

        return data

    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 400:
            print_error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print_error(f"Results retrieval failed: {e}")
        return None


def test_invalid_job_id() -> bool:
    """Test error handling with invalid job ID"""
    print_header("TEST 8: Error Handling (Invalid Job ID)")

    fake_job_id = "00000000-0000-0000-0000-000000000000"
    print_info(f"Testing with invalid job ID: {fake_job_id}")

    try:
        response = requests.get(f"{API_BASE_URL}/jobs/{fake_job_id}", timeout=10)

        if response.status_code == 404:
            print_success("Correctly returned 404 for invalid job ID")
            return True
        else:
            print_error(f"Expected 404, got {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error handling test failed: {e}")
        return False


def test_start_job_without_upload(job_id: str) -> bool:
    """Test starting a job without uploading the file first"""
    print_header("TEST 9: Error Handling (Start Without Upload)")

    # Create a new job but don't upload
    payload = {"audio_filename": "never-uploaded.wav", "workflow_type": "transcribe_only", "source_language": "en"}

    try:
        create_response = requests.post(f"{API_BASE_URL}/jobs", json=payload, timeout=10)
        create_response.raise_for_status()
        new_job_id = create_response.json().get("job_id")

        print_info(f"Created job {new_job_id} without uploading file")

        # Try to start without upload
        start_response = requests.post(f"{API_BASE_URL}/jobs/{new_job_id}/start", timeout=10)

        if start_response.status_code == 400:
            error_data = start_response.json()
            if "not found" in error_data.get("detail", "").lower():
                print_success("Correctly rejected job start without uploaded file")
                return True

        print_error(f"Expected 400 error, got {start_response.status_code}")
        return False

    except Exception as e:
        print_error(f"Error handling test failed: {e}")
        return False


def run_full_integration_test():
    """Run the complete integration test suite"""
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "SPEECH-FLOW LOCAL INTEGRATION TEST" + " " * 29 + "║")
    print("║" + " " * 78 + "║")
    print("║" + f"  API: {API_BASE_URL}" + " " * (76 - len(API_BASE_URL) - 8) + "║")
    print("║" + f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + " " * 51 + "║")
    print("╚" + "═" * 78 + "╝")
    print(f"{Colors.ENDC}\n")

    results = {"passed": 0, "failed": 0, "skipped": 0, "total": 0}

    # Test 1: Health Check
    results["total"] += 1
    if test_health_check():
        results["passed"] += 1
    else:
        results["failed"] += 1
        print_error("Aborting: API is not healthy")
        print_final_results(results)
        return

    # Generate test audio
    audio_bytes = generate_test_audio()

    # Test 2: Create Job
    results["total"] += 1
    job_info = test_create_job(workflow_type="transcribe_only", source_language="en")
    if job_info:
        results["passed"] += 1
        job_id = job_info["job_id"]
        upload_url = job_info["upload_url"]
    else:
        results["failed"] += 1
        print_error("Aborting: Job creation failed")
        print_final_results(results)
        return

    # Test 3: Upload Audio
    results["total"] += 1
    if test_upload_audio(upload_url, audio_bytes):
        results["passed"] += 1
    else:
        results["failed"] += 1
        print_warning("Continuing despite upload failure...")

    # Test 4: Start Job
    results["total"] += 1
    if test_start_job(job_id):
        results["passed"] += 1
    else:
        results["failed"] += 1
        print_warning("Continuing despite start failure...")

    # Test 5: Get Job Status
    results["total"] += 1
    status_data = test_get_job_status(job_id, expected_status="queued")
    if status_data:
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 6: List Jobs
    results["total"] += 1
    if test_list_jobs(limit=10):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 7: Get Results (expected to fail if workers not running)
    results["total"] += 1
    result_data = test_get_job_results(job_id)
    if result_data:
        results["passed"] += 1
    else:
        print_info("Results not available (expected if workers are not running)")
        results["skipped"] += 1

    # Test 8: Invalid Job ID
    results["total"] += 1
    if test_invalid_job_id():
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 9: Start Without Upload
    results["total"] += 1
    if test_start_job_without_upload(job_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Print final results
    print_final_results(results)


def print_final_results(results: Dict[str, int]):
    """Print final test results summary"""
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 30 + "TEST SUMMARY" + " " * 36 + "║")
    print("╠" + "═" * 78 + "╣")

    passed = results["passed"]
    failed = results["failed"]
    skipped = results["skipped"]
    total = results["total"]

    pass_color = Colors.OKGREEN if passed > 0 else Colors.ENDC
    fail_color = Colors.FAIL if failed > 0 else Colors.ENDC
    skip_color = Colors.WARNING if skipped > 0 else Colors.ENDC

    print(f"║  {pass_color}✓ Passed:  {passed:2d}{Colors.OKBLUE}" + " " * 64 + "║")
    print(f"║  {fail_color}✗ Failed:  {failed:2d}{Colors.OKBLUE}" + " " * 64 + "║")
    print(f"║  {skip_color}⊘ Skipped: {skipped:2d}{Colors.OKBLUE}" + " " * 64 + "║")
    print(f"║  {'─' * 12}" + " " * 64 + "║")
    print(f"║  Total:    {total:2d}" + " " * 64 + "║")
    print("╠" + "═" * 78 + "╣")

    if failed == 0 and passed > 0:
        status = f"{Colors.OKGREEN}ALL TESTS PASSED{Colors.OKBLUE}"
    elif failed > 0:
        status = f"{Colors.FAIL}SOME TESTS FAILED{Colors.OKBLUE}"
    else:
        status = f"{Colors.WARNING}NO TESTS RAN{Colors.OKBLUE}"

    print(
        "║"
        + " " * 29
        + status
        + " "
        * (
            49
            - len(
                status.replace(Colors.OKGREEN, "")
                .replace(Colors.FAIL, "")
                .replace(Colors.WARNING, "")
                .replace(Colors.OKBLUE, "")
            )
        )
        + "║"
    )
    print("╚" + "═" * 78 + "╝")
    print(f"{Colors.ENDC}\n")


if __name__ == "__main__":
    try:
        run_full_integration_test()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test interrupted by user{Colors.ENDC}\n")
    except Exception as e:
        print(f"\n{Colors.FAIL}Unexpected error: {e}{Colors.ENDC}\n")
        raise
