"""
Speech Processing API - Python Client SDK (Updated)
Production-ready implementation with DefaultAzureCredential for blob access
Supports: Service Principal (env vars) + User-Assigned Managed Identity (UAMI)
"""

import time
import json
import requests
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid
from pathlib import Path
from urllib.parse import urlparse

# Azure SDK imports
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(Enum):
    TRANSCRIPTION = "transcription"
    LANGUAGE_DETECTION = "language_detection"
    TRANSLATION = "translation"
    TEXT_TO_SPEECH = "text_to_speech"


@dataclass
class APIError(Exception):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None

    def __str__(self):
        return f"[{self.code}] {self.message}"


@dataclass
class BlobSource:
    storage_account_name: str
    container_name: str
    blob_name: str
    type: str = "azure_blob"


@dataclass
class TranscriptionJob:
    job_id: str
    status: JobStatus
    text: Optional[str] = None
    segments: Optional[List[Dict]] = None
    processing_time_seconds: Optional[float] = None
    download_url: Optional[str] = None
    error: Optional[APIError] = None


@dataclass
class LanguageDetectionJob:
    job_id: str
    status: JobStatus
    primary_language: Optional[str] = None
    languages: Optional[List[Dict]] = None
    error: Optional[APIError] = None


class SpeechProcessingAPI:
    """
    Client for Speech Processing API with OAuth2 authentication
    and DefaultAzureCredential for blob operations.
    
    Supports multiple credential types:
    - Service Principal (via environment variables)
    - User-Assigned Managed Identity (UAMI)
    - System-Assigned Managed Identity (fallback in Azure)
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        api_endpoint: str = "https://api.speechapi.dev/v1",
        auth_endpoint: str = "https://auth.speechapi.dev/oauth/token",
        storage_account_name: str = "speechapistorage",
        storage_account_url: Optional[str] = None,
        managed_identity_client_id: Optional[str] = None,
    ):
        """
        Initialize API client.

        Args:
            client_id: OAuth2 client ID (for API authentication)
            client_secret: OAuth2 client secret (for API authentication)
            api_endpoint: Base API endpoint
            auth_endpoint: OAuth2 token endpoint
            storage_account_name: Azure Storage account name
            storage_account_url: Optional custom storage account URL (default: https://{account_name}.blob.core.windows.net)
            managed_identity_client_id: Optional UAMI client ID for DefaultAzureCredential
                                       (if None, uses environment AZURE_CLIENT_ID or system-assigned MI)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_endpoint = api_endpoint
        self.auth_endpoint = auth_endpoint
        self.storage_account_name = storage_account_name
        self.managed_identity_client_id = managed_identity_client_id
        
        # Construct storage account URL
        if storage_account_url:
            self.storage_account_url = storage_account_url
        else:
            self.storage_account_url = f"https://{storage_account_name}.blob.core.windows.net"
        
        self._access_token = None
        self._token_expiry = None
        self.session = requests.Session()
        
        # Initialize Azure Identity (DefaultAzureCredential)
        self.credential = self._init_credential()
        self.blob_client = self._init_blob_client()

    def _init_credential(self):
        """Initialize DefaultAzureCredential."""
        try:
            if self.managed_identity_client_id:
                print(f"[DEBUG] Initializing DefaultAzureCredential with UAMI: {self.managed_identity_client_id}")
                return DefaultAzureCredential(
                    managed_identity_client_id=self.managed_identity_client_id
                )
            else:
                print("[DEBUG] Initializing DefaultAzureCredential (auto-detect mode)")
                return DefaultAzureCredential()
        except Exception as e:
            raise APIError(
                code="CREDENTIAL_INIT_FAILED",
                message=f"Failed to initialize Azure credentials: {str(e)}",
            )

    def _init_blob_client(self) -> BlobServiceClient:
        """Initialize Azure Blob Storage client with DefaultAzureCredential."""
        try:
            print(f"[DEBUG] Initializing BlobServiceClient for {self.storage_account_url}")
            return BlobServiceClient(
                account_url=self.storage_account_url,
                credential=self.credential
            )
        except Exception as e:
            raise APIError(
                code="BLOB_CLIENT_INIT_FAILED",
                message=f"Failed to initialize blob client: {str(e)}",
            )

    def _get_access_token(self) -> str:
        """Obtain or refresh OAuth2 access token for API authentication."""
        if self._access_token and self._token_expiry and self._token_expiry > datetime.utcnow():
            return self._access_token

        response = self.session.post(
            self.auth_endpoint,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "speech.transcribe speech.translate speech.detect speech.synthesize",
            },
        )

        if response.status_code != 200:
            raise APIError(
                code="AUTH_FAILED",
                message=f"Failed to obtain access token: {response.text}",
            )

        token_data = response.json()
        self._access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 300)

        return self._access_token

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make authenticated API request."""
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self._get_access_token()}"
        kwargs["headers"] = headers

        url = f"{self.api_endpoint}{endpoint}"
        response = self.session.request(method, url, **kwargs)

        if response.status_code >= 400:
            try:
                error_data = response.json().get("error", {})
                raise APIError(
                    code=error_data.get("code", "UNKNOWN_ERROR"),
                    message=error_data.get("message", response.text),
                    details=error_data.get("details"),
                )
            except json.JSONDecodeError:
                raise APIError(
                    code=f"HTTP_{response.status_code}",
                    message=response.text,
                )

        return response.json()

    def upload_to_blob(
        self,
        file_path: str,
        container_name: str = "audio-uploads",
        blob_name: Optional[str] = None,
    ) -> BlobSource:
        """
        Upload audio file to Azure Blob Storage using DefaultAzureCredential.
        
        Returns:
            BlobSource object containing storage details for the API.
        """
        try:
            # Ensure container exists
            container_client = self.blob_client.get_container_client(container_name)
            try:
                container_client.get_container_properties()
            except:
                print(f"[DEBUG] Creating container: {container_name}")
                self.blob_client.create_container(name=container_name)
            
            # Generate blob name if not provided
            if not blob_name:
                file_obj = Path(file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                blob_name = f"{timestamp}_{file_obj.name}"
            
            # Upload file
            with open(file_path, "rb") as data:
                print(f"[DEBUG] Uploading to blob: {blob_name}")
                container_client.upload_blob(blob_name, data, overwrite=True)
            
            print(f"[DEBUG] Upload successful: {container_name}/{blob_name}")
            
            return BlobSource(
                storage_account_name=self.storage_account_name,
                container_name=container_name,
                blob_name=blob_name
            )
            
        except Exception as e:
            raise APIError(
                code="BLOB_UPLOAD_FAILED",
                message=f"Failed to upload to blob: {str(e)}",
            )

    def download_from_blob(
        self,
        blob_uri: str,
        output_path: str,
    ) -> None:
        """Download result from Azure Blob Storage using DefaultAzureCredential."""
        try:
            # Parse blob URI to get container and full blob path
            # Format: https://account.blob.core.windows.net/container/path/to/blob
            parsed = urlparse(blob_uri)
            path_parts = parsed.path.lstrip("/").split("/", 1)
            if len(path_parts) != 2:
                raise ValueError(f"Invalid blob uri format: {blob_uri}")
            container_name, blob_path = path_parts
            
            print(f"[DEBUG] Downloading blob: {container_name}/{blob_path}")
            blob_client = self.blob_client.get_blob_client(
                container=container_name,
                blob=blob_path
            )
            
            with open(output_path, "wb") as file:
                file.write(blob_client.download_blob().readall())
            
            print(f"[DEBUG] Download successful: {output_path}")
            
        except Exception as e:
            raise APIError(
                code="BLOB_DOWNLOAD_FAILED",
                message=f"Failed to download from blob: {str(e)}",
            )

    def process_audio(
        self,
        audio_source: Union[BlobSource, str],
        language: str = "auto",
        model: str = "whisper-large-v3",
        target_languages: Optional[List[str]] = None,
        diarization_enabled: bool = False,
        auto_poll: bool = True,
        poll_timeout_seconds: int = 3600,
    ) -> TranscriptionJob:
        """
        Unified Pipeline: Detect + Transcribe + Translate.
        Uses /stt/process endpoint.
        
        Args:
            audio_source: BlobSource object or path to local file (will be uploaded)
            language: Source language code or 'auto'
            model: whisper-large-v3 or azure-speech-standard
            target_languages: List of languages to translate to
            diarization_enabled: Enable speaker diarization
        """
        # Handle local file upload if string path provided
        if isinstance(audio_source, str):
            print(f"[DEBUG] Uploading local file: {audio_source}")
            audio_source = self.upload_to_blob(audio_source)

        payload = {
            "audio_source": asdict(audio_source),
            "config": {
                "language": language,
                "model": model,
                "diarization": {"enabled": diarization_enabled},
                "translation": {"target_languages": target_languages} if target_languages else None
            }
        }

        response = self._make_request("POST", "/stt/process", json=payload)

        job = TranscriptionJob(
            job_id=response["job_id"],
            status=JobStatus(response["status"]),
        )

        if auto_poll:
            return self.poll_transcription_job(job.job_id, timeout_seconds=poll_timeout_seconds)

        return job

    def stream_speech(
        self,
        text: str,
        language: str = "en-US",
        voice_id: str = "en-US-AriaNeural",
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Real-time TTS Streaming.
        Uses /tts/stream endpoint.
        """
        payload = {
            "text": text,
            "language": language,
            "voice_id": voice_id,
            "audio_format": "mp3"
        }

        # Use raw session request to handle binary stream
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}
        url = f"{self.api_endpoint}/tts/stream"
        
        response = self.session.post(url, json=payload, headers=headers, stream=True)
        
        if response.status_code != 200:
            raise APIError(code=f"HTTP_{response.status_code}", message=response.text)

        audio_data = response.content
        
        if output_path:
            with open(output_path, "wb") as f:
                f.write(audio_data)
            print(f"[DEBUG] Streamed audio saved to: {output_path}")
            
        return audio_data

    def synthesize_batch(
        self,
        text: str,
        language: str,
        voice_id: str,
        auto_poll: bool = True,
    ) -> Dict[str, Any]:
        """Batch TTS Synthesis (Async)."""
        payload = {
            "text": text,
            "language": language,
            "voice_id": voice_id,
        }

        response = self._make_request("POST", "/text-to-speech/synthesize", json=payload)

        if auto_poll:
            return self._poll_tts_job(response["job_id"])

        return response

    def poll_transcription_job(
        self,
        job_id: str,
        timeout_seconds: int = 3600,
    ) -> TranscriptionJob:
        """Poll transcription job until completion."""
        backoff = 1.0
        elapsed = 0

        while elapsed < timeout_seconds:
            response = self._make_request("GET", f"/jobs/{job_id}")
            
            status = JobStatus(response["status"])
            
            if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                return TranscriptionJob(
                    job_id=response["job_id"],
                    status=status,
                    text=response.get("text"),
                    download_url=response.get("download_url"),
                    error=response.get("error")
                )

            print(f"Job {job_id}: {status.value} - Waiting {backoff}s...")
            time.sleep(backoff)
            elapsed += backoff
            backoff = min(backoff * 1.5, 30.0)

        raise TimeoutError(f"Job {job_id} timed out")

    def _poll_tts_job(self, job_id: str, timeout_seconds: int = 300) -> Dict[str, Any]:
        """Poll TTS job until completion."""
        backoff = 1.0
        elapsed = 0
        while elapsed < timeout_seconds:
            response = self._make_request("GET", f"/jobs/{job_id}")
            if response["status"] in ["completed", "failed"]:
                return response
            time.sleep(backoff)
            elapsed += backoff
            backoff = min(backoff * 1.5, 30.0)
        raise TimeoutError(f"TTS job {job_id} timed out")

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("=== Speech Processing API Client Demo ===")
    
    client = SpeechProcessingAPI(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        storage_account_name="speechapistorage"
    )

    # 1. Unified Pipeline (Upload -> Detect -> Transcribe -> Translate)
    print("\n--- 1. Unified Pipeline ---")
    try:
        job = client.process_audio(
            audio_source="meeting.wav",  # Auto-uploads to blob
            language="auto",
            target_languages=["es-ES", "de-DE"],
            diarization_enabled=True
        )
        if job.text:
            print(f"Result: {job.text[:50]}...")
        else:
            print("Job completed but no text returned.")
    except Exception as e:
        print(f"Skipping (No auth): {e}")

    # 2. Real-Time TTS Streaming
    print("\n--- 2. Real-Time TTS ---")
    try:
        client.stream_speech(
            text="Hello, this is a real-time stream.",
            output_path="stream_output.mp3"
        )
    except Exception as e:
        print(f"Skipping (No auth): {e}")
