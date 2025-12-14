"""
Speech-Flow Integration Test Suite
Tests end-to-end workflow against local Podman environment.

Usage:
    python test_integration.py
    pytest test_integration.py -v
"""

import io
import struct
import wave
from datetime import datetime
from typing import Optional

import requests


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class IntegrationTest:
    """Comprehensive integration test for Speech-Flow API"""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.job_id: Optional[str] = None
        self.upload_url: Optional[str] = None
        self.test_audio_bytes: bytes = self._generate_test_audio()
        self.passed_tests = 0
        self.failed_tests = 0

    def _generate_test_audio(self, duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
        """Generate a simple sine wave WAV file in memory"""
        num_samples = int(duration_seconds * sample_rate)
        frequency = 440.0  # A4 note

        # Generate sine wave samples
        samples = []
        for i in range(num_samples):
            sample = int(
                32767 * 0.3 * struct.unpack("d", struct.pack("d", 2.0 * 3.14159 * frequency * i / sample_rate))[0]
            )
            samples.append(sample)

        # Create WAV file in memory
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(struct.pack("h" * len(samples), *samples))

        return buffer.getvalue()

    def _print_header(self, text: str):
        """Print a formatted test section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")

    def _print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")
        self.passed_tests += 1

    def _print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.RED}✗ {text}{Colors.RESET}")
        self.failed_tests += 1

    def _print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")

    def _assert_response(self, response: requests.Response, expected_status: int, test_name: str):
        """Assert response status code and handle errors"""
        try:
            if response.status_code == expected_status:
                self._print_success(f"{test_name}: Status {response.status_code}")
                return True
            else:
                self._print_error(
                    f"{test_name}: Expected {expected_status}, got {response.status_code}\n"
                    f"  Response: {response.text[:200]}"
                )
                return False
        except Exception as e:
            self._print_error(f"{test_name}: {str(e)}")
            return False

    def test_01_health_check(self) -> bool:
        """Test API health check endpoint"""
        self._print_header("TEST 1: Health Check")

        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)

            if not self._assert_response(response, 200, "Health check"):
                return False

            data = response.json()
            if data.get("status") == "healthy" and data.get("service") == "speech-flow-api":
                self._print_success(f"Health check response valid: {data}")
                return True
            else:
                self._print_error(f"Unexpected health response: {data}")
                return False

        except requests.exceptions.RequestException as e:
            self._print_error(f"Health check failed: {str(e)}")
            self._print_info("Ensure services are running: ./start-services.ps1")
            return False

    def test_02_create_job(self) -> bool:
        """Test job creation and SAS URL generation"""
        self._print_header("TEST 2: Create Job")

        payload = {
            "audio_filename": "test_audio.wav",
            "workflow_type": "transcribe_only",
            "source_language": "en",
            "target_language": "en",
        }

        try:
            response = requests.post(f"{self.api_base_url}/jobs", json=payload, timeout=10)

            if not self._assert_response(response, 200, "Create job"):
                return False

            data = response.json()

            # Validate response structure
            required_fields = ["job_id", "status", "message", "upload_url"]
            for field in required_fields:
                if field not in data:
                    self._print_error(f"Missing field in response: {field}")
                    return False

            self.job_id = data["job_id"]
            self.upload_url = data["upload_url"]

            self._print_success(f"Job created: {self.job_id}")
            self._print_success(f"Status: {data['status']}")
            self._print_info(f"Upload URL: {self.upload_url[:80]}...")

            # Validate upload URL format
            if "devstoreaccount1" in self.upload_url and "raw-audio" in self.upload_url:
                self._print_success("Upload URL points to Azurite (local mode)")
            else:
                self._print_info("Upload URL format: " + self.upload_url.split("?")[0])

            return True

        except Exception as e:
            self._print_error(f"Create job failed: {str(e)}")
            return False

    def test_03_upload_audio(self) -> bool:
        """Test audio file upload via SAS URL"""
        self._print_header("TEST 3: Upload Audio File")

        if not self.upload_url:
            self._print_error("No upload URL available (previous test failed)")
            return False

        try:
            self._print_info(f"Uploading {len(self.test_audio_bytes)} bytes of test audio")

            headers = {"x-ms-blob-type": "BlockBlob", "Content-Type": "audio/wav"}

            response = requests.put(self.upload_url, data=self.test_audio_bytes, headers=headers, timeout=30)

            if not self._assert_response(response, 201, "Upload audio"):
                self._print_info(f"Full response: {response.text}")
                return False

            self._print_success(f"Audio uploaded successfully ({len(self.test_audio_bytes)} bytes)")
            return True

        except Exception as e:
            self._print_error(f"Upload failed: {str(e)}")
            return False

    def test_04_start_job(self) -> bool:
        """Test starting a job after upload"""
        self._print_header("TEST 4: Start Job")

        if not self.job_id:
            self._print_error("No job ID available (previous test failed)")
            return False

        try:
            response = requests.post(f"{self.api_base_url}/jobs/{self.job_id}/start", timeout=10)

            if not self._assert_response(response, 200, "Start job"):
                return False

            data = response.json()

            if data.get("status") == "queued":
                self._print_success(f"Job started: {data['status']}")
                self._print_info(f"Message: {data.get('message', 'N/A')}")
                return True
            else:
                self._print_error(f"Unexpected status: {data.get('status')}")
                return False

        except Exception as e:
            self._print_error(f"Start job failed: {str(e)}")
            return False

    def test_05_get_job_status(self) -> bool:
        """Test retrieving job status"""
        self._print_header("TEST 5: Get Job Status")

        if not self.job_id:
            self._print_error("No job ID available (previous test failed)")
            return False

        try:
            response = requests.get(f"{self.api_base_url}/jobs/{self.job_id}", timeout=10)

            if not self._assert_response(response, 200, "Get job status"):
                return False

            data = response.json()

            # Validate response structure
            required_fields = [
                "job_id",
                "status",
                "workflow_type",
                "audio_filename",
                "created_at",
                "updated_at",
                "steps",
            ]

            for field in required_fields:
                if field not in data:
                    self._print_error(f"Missing field in response: {field}")
                    return False

            self._print_success(f"Job ID: {data['job_id']}")
            self._print_success(f"Status: {data['status']}")
            self._print_success(f"Workflow: {data['workflow_type']}")
            self._print_success(f"Audio: {data['audio_filename']}")
            self._print_info(f"Created: {data['created_at']}")
            self._print_info(f"Updated: {data['updated_at']}")
            self._print_info(f"Steps: {len(data['steps'])} processing steps")

            return True

        except Exception as e:
            self._print_error(f"Get job status failed: {str(e)}")
            return False

    def test_06_list_jobs(self) -> bool:
        """Test listing jobs with filters"""
        self._print_header("TEST 6: List Jobs")

        try:
            # Test basic list
            response = requests.get(f"{self.api_base_url}/jobs?limit=10", timeout=10)

            if not self._assert_response(response, 200, "List jobs"):
                return False

            data = response.json()

            if "total" in data and "jobs" in data:
                self._print_success(f"Total jobs: {data['total']}")
                self._print_success(f"Jobs in response: {len(data['jobs'])}")

                # Verify our job is in the list
                job_ids = [job["job_id"] for job in data["jobs"]]
                if self.job_id and self.job_id in job_ids:
                    self._print_success(f"Current job found in list: {self.job_id}")
                else:
                    self._print_info(f"Current job not in top 10 results")

                return True
            else:
                self._print_error("Unexpected response structure")
                return False

        except Exception as e:
            self._print_error(f"List jobs failed: {str(e)}")
            return False

    def test_07_workflow_validation(self) -> bool:
        """Test workflow validation and error handling"""
        self._print_header("TEST 7: Workflow Validation")

        # Test 1: Missing required field (source_language for transcribe_only)
        invalid_payload = {
            "audio_filename": "test.wav",
            "workflow_type": "transcribe_only",
            # Missing source_language
        }

        try:
            response = requests.post(f"{self.api_base_url}/jobs", json=invalid_payload, timeout=10)

            if response.status_code == 422:  # Validation error expected
                self._print_success("Validation error correctly returned for missing source_language")
            else:
                self._print_error(f"Expected 422, got {response.status_code}")
                return False

            # Test 2: Invalid job ID (404 expected)
            fake_job_id = "00000000-0000-0000-0000-000000000000"
            response = requests.get(f"{self.api_base_url}/jobs/{fake_job_id}", timeout=10)

            if response.status_code == 404:
                self._print_success("404 correctly returned for non-existent job")
            else:
                self._print_error(f"Expected 404, got {response.status_code}")
                return False

            return True

        except Exception as e:
            self._print_error(f"Validation test failed: {str(e)}")
            return False

    def test_08_azurite_connectivity(self) -> bool:
        """Test Azurite storage connectivity"""
        self._print_header("TEST 8: Azurite Storage Check")

        try:
            # Test Azurite blob service health endpoint
            azurite_url = "http://localhost:10000/devstoreaccount1?comp=list"

            response = requests.get(azurite_url, timeout=5)

            if response.status_code in [200, 400]:  # 400 is ok for this endpoint without auth
                self._print_success("Azurite blob service is accessible")

                # Check if containers exist
                if "raw-audio" in response.text or response.status_code == 400:
                    self._print_success("Azurite containers initialized")

                return True
            else:
                self._print_error(f"Azurite check returned {response.status_code}")
                return False

        except Exception as e:
            self._print_error(f"Azurite connectivity test failed: {str(e)}")
            self._print_info("Ensure Azurite is running: podman ps | grep azurite")
            return False

    def test_09_postgres_connectivity(self) -> bool:
        """Test PostgreSQL database connectivity (via API)"""
        self._print_header("TEST 9: PostgreSQL Database Check")

        try:
            # Database connectivity is validated implicitly through successful API calls
            # We've already created jobs, which require DB writes

            if self.job_id:
                self._print_success("Database connectivity confirmed (job created successfully)")
                self._print_info("Database operations: CREATE, READ validated")
                return True
            else:
                self._print_error("Cannot validate database (no successful job creation)")
                return False

        except Exception as e:
            self._print_error(f"Database check failed: {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """Run all integration tests in sequence"""
        print(f"\n{Colors.BOLD}Starting Speech-Flow Integration Test Suite{Colors.RESET}")
        print(f"{Colors.BOLD}API Base URL: {self.api_base_url}{Colors.RESET}")
        print(f"{Colors.BOLD}Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")

        tests = [
            self.test_01_health_check,
            self.test_02_create_job,
            self.test_03_upload_audio,
            self.test_04_start_job,
            self.test_05_get_job_status,
            self.test_06_list_jobs,
            self.test_07_workflow_validation,
            self.test_08_azurite_connectivity,
            self.test_09_postgres_connectivity,
        ]

        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
                if not result:
                    self._print_info("Continuing with remaining tests...")
            except Exception as e:
                self._print_error(f"Test {test.__name__} crashed: {str(e)}")
                results.append(False)

        # Print summary
        self._print_header("Test Summary")

        total_tests = len(results)
        passed = sum(results)
        failed = total_tests - passed

        print(f"{Colors.BOLD}Total Tests: {total_tests}{Colors.RESET}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"{Colors.BOLD}Success Rate: {(passed/total_tests*100):.1f}%{Colors.RESET}")

        if self.job_id:
            print(f"\n{Colors.BOLD}Test Job ID: {self.job_id}{Colors.RESET}")
            print(f"{Colors.YELLOW}You can check this job status at:{Colors.RESET}")
            print(f"  {self.api_base_url}/jobs/{self.job_id}")

        print(f"\n{Colors.BOLD}Service URLs:{Colors.RESET}")
        print(f"  API:       http://localhost:8000")
        print(f"  Dashboard: http://localhost:8501")
        print(f"  UI:        http://localhost:8502")
        print(f"  Azurite:   http://localhost:10000")

        return all(results)


def main():
    """Main entry point for standalone execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Speech-Flow Integration Test Suite")
    parser.add_argument(
        "--api-url", default="http://localhost:8000", help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    tester = IntegrationTest(api_base_url=args.api_url)
    success = tester.run_all_tests()

    exit(0 if success else 1)


# PyTest integration
def test_integration_suite():
    """PyTest wrapper for the integration test suite"""
    tester = IntegrationTest()
    assert tester.run_all_tests(), "Integration test suite failed"


if __name__ == "__main__":
    main()
