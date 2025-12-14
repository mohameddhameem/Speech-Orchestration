"""Storage adapter to support both Azure Blob Storage and local filesystem.

This module provides a unified interface for storage operations that works with:
- Azure Blob Storage (using DefaultAzureCredential)
- Local filesystem (for development)
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional


class StorageAdapter(ABC):
    """Abstract base class for storage adapters."""

    @abstractmethod
    def upload_blob(self, container_name: str, blob_name: str, data: bytes, overwrite: bool = True) -> None:
        """Upload data to storage.

        Args:
            container_name: Name of the container/directory
            blob_name: Name of the blob/file
            data: Binary data to upload
            overwrite: Whether to overwrite existing data
        """
        pass

    @abstractmethod
    def download_blob(self, container_name: str, blob_name: str) -> bytes:
        """Download data from storage.

        Args:
            container_name: Name of the container/directory
            blob_name: Name of the blob/file

        Returns:
            Binary data from storage
        """
        pass

    @abstractmethod
    def blob_exists(self, container_name: str, blob_name: str) -> bool:
        """Check if blob exists.

        Args:
            container_name: Name of the container/directory
            blob_name: Name of the blob/file

        Returns:
            True if blob exists, False otherwise
        """
        pass

    @abstractmethod
    def ensure_container(self, container_name: str) -> None:
        """Ensure container/directory exists.

        Args:
            container_name: Name of the container/directory to create
        """
        pass

    @abstractmethod
    def generate_upload_url(self, container_name: str, blob_name: str) -> str:
        """Generate upload URL (SAS for Azure, file path for local).

        Args:
            container_name: Name of the container/directory
            blob_name: Name of the blob/file

        Returns:
            URL or path for uploading
        """
        pass


class AzureBlobStorageAdapter(StorageAdapter):
    """Azure Blob Storage implementation using DefaultAzureCredential."""

    def __init__(
        self,
        account_url: Optional[str] = None,
        use_connection_string: bool = False,
        connection_string: Optional[str] = None,
    ):
        """Initialize Azure Blob Storage adapter.

        Args:
            account_url: Azure Storage account URL
            use_connection_string: Whether to use connection string (for Azurite)
            connection_string: Connection string (only for Azurite development)
        """
        from azure.storage.blob import BlobServiceClient

        self.account_url = account_url
        self.use_connection_string = use_connection_string

        if use_connection_string and connection_string:
            # Use connection string (for Azurite local development)
            self.client = BlobServiceClient.from_connection_string(connection_string)
        else:
            # Use DefaultAzureCredential (production)
            from azure.identity import DefaultAzureCredential

            credential = DefaultAzureCredential()
            self.client = BlobServiceClient(account_url=account_url, credential=credential)

    def upload_blob(self, container_name: str, blob_name: str, data: bytes, overwrite: bool = True) -> None:
        """Upload data to Azure Blob Storage."""
        blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.upload_blob(data, overwrite=overwrite)

    def download_blob(self, container_name: str, blob_name: str) -> bytes:
        """Download data from Azure Blob Storage."""
        blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
        return blob_client.download_blob().readall()

    def blob_exists(self, container_name: str, blob_name: str) -> bool:
        """Check if blob exists in Azure."""
        blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
        return blob_client.exists()

    def ensure_container(self, container_name: str) -> None:
        """Ensure container exists in Azure."""
        container_client = self.client.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()

    def generate_upload_url(self, container_name: str, blob_name: str) -> str:
        """Generate SAS URL for uploading."""
        if self.use_connection_string:
            # For Azurite, generate SAS with connection string
            from azure.storage.blob import BlobSasPermissions, generate_blob_sas

            sas_token = generate_blob_sas(
                account_name=self.client.account_name,
                container_name=container_name,
                blob_name=blob_name,
                account_key=self.client.credential.account_key,
                permission=BlobSasPermissions(write=True, create=True),
                expiry=datetime.utcnow() + timedelta(hours=1),
            )

            # For Azurite, use localhost endpoint accessible from host
            if self.client.account_name == "devstoreaccount1":
                base_url = "http://localhost:10000/devstoreaccount1"
            else:
                base_url = self.client.url.rstrip("/")

            return f"{base_url}/{container_name}/{blob_name}?{sas_token}"
        else:
            # For production with DefaultAzureCredential, generate user delegation SAS
            from azure.storage.blob import BlobSasPermissions, UserDelegationKey, generate_blob_sas

            # Get user delegation key
            delegation_key = self.client.get_user_delegation_key(
                key_start_time=datetime.utcnow(), key_expiry_time=datetime.utcnow() + timedelta(hours=1)
            )

            sas_token = generate_blob_sas(
                account_name=self.client.account_name,
                container_name=container_name,
                blob_name=blob_name,
                user_delegation_key=delegation_key,
                permission=BlobSasPermissions(write=True, create=True),
                expiry=datetime.utcnow() + timedelta(hours=1),
            )

            return f"{self.account_url}/{container_name}/{blob_name}?{sas_token}"


class LocalFileStorageAdapter(StorageAdapter):
    """Local filesystem implementation for development."""

    def __init__(self, base_path: str = "/tmp/speech-flow-storage"):
        """Initialize local storage adapter.

        Args:
            base_path: Base directory for local storage
        """
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _get_blob_path(self, container_name: str, blob_name: str) -> str:
        """Get full file path for a blob.

        Args:
            container_name: Container directory name
            blob_name: Blob file name

        Returns:
            Full file path
        """
        container_path = os.path.join(self.base_path, container_name)
        os.makedirs(container_path, exist_ok=True)
        return os.path.join(container_path, blob_name)

    def upload_blob(self, container_name: str, blob_name: str, data: bytes, overwrite: bool = True) -> None:
        """Upload data to local filesystem."""
        blob_path = self._get_blob_path(container_name, blob_name)

        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(blob_path), exist_ok=True)

        # Write file
        mode = "wb" if overwrite else "xb"
        with open(blob_path, mode) as f:
            f.write(data)

    def download_blob(self, container_name: str, blob_name: str) -> bytes:
        """Download data from local filesystem."""
        blob_path = self._get_blob_path(container_name, blob_name)
        with open(blob_path, "rb") as f:
            return f.read()

    def blob_exists(self, container_name: str, blob_name: str) -> bool:
        """Check if file exists."""
        blob_path = self._get_blob_path(container_name, blob_name)
        return os.path.exists(blob_path)

    def ensure_container(self, container_name: str) -> None:
        """Ensure directory exists."""
        container_path = os.path.join(self.base_path, container_name)
        os.makedirs(container_path, exist_ok=True)

    def generate_upload_url(self, container_name: str, blob_name: str) -> str:
        """Generate file path for uploading (local mode).

        Args:
            container_name: Container directory name
            blob_name: Blob file name

        Returns:
            File path URL
        """
        blob_path = self._get_blob_path(container_name, blob_name)
        # Create parent directories
        os.makedirs(os.path.dirname(blob_path), exist_ok=True)
        return f"file://{blob_path}"


def get_storage_adapter(account_url: Optional[str] = None, connection_string: Optional[str] = None) -> StorageAdapter:
    """Factory function to get the appropriate storage adapter.

    Args:
        account_url: Azure Storage account URL (for AZURE mode)
        connection_string: Connection string (for Azurite development)

    Returns:
        StorageAdapter instance (either Azure Blob Storage or local filesystem)
    """
    environment = os.getenv("ENVIRONMENT", "AZURE").upper()

    # Check if connection string provided
    if connection_string is None:
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")

    # Check if this is Azurite (connection string with devstoreaccount1)
    use_azurite = "devstoreaccount1" in connection_string or "BlobEndpoint=http://" in connection_string

    if environment == "LOCAL" and not use_azurite:
        # Use local filesystem for local development (no Azurite)
        base_path = os.getenv("LOCAL_STORAGE_PATH", "/tmp/speech-flow-storage")
        return LocalFileStorageAdapter(base_path)
    elif use_azurite:
        # Use Azurite with connection string (LOCAL mode with Azurite)
        return AzureBlobStorageAdapter(use_connection_string=True, connection_string=connection_string)
    else:
        # Production: Use Azure Blob Storage with DefaultAzureCredential
        if account_url is None:
            account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL", "")
        return AzureBlobStorageAdapter(account_url=account_url, use_connection_string=False)
