"""
Storage adapter to support both Azure Blob Storage and local filesystem
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime, timedelta


class StorageAdapter(ABC):
    """Abstract base class for storage adapters"""
    
    @abstractmethod
    def upload_blob(self, container_name: str, blob_name: str, data: bytes, overwrite: bool = True):
        """Upload data to storage"""
        pass
    
    @abstractmethod
    def download_blob(self, container_name: str, blob_name: str) -> bytes:
        """Download data from storage"""
        pass
    
    @abstractmethod
    def blob_exists(self, container_name: str, blob_name: str) -> bool:
        """Check if blob exists"""
        pass
    
    @abstractmethod
    def ensure_container(self, container_name: str):
        """Ensure container/directory exists"""
        pass
    
    @abstractmethod
    def generate_upload_url(self, container_name: str, blob_name: str) -> str:
        """Generate upload URL (SAS for Azure, file path for local)"""
        pass


class AzureBlobStorageAdapter(StorageAdapter):
    """Azure Blob Storage implementation"""
    
    def __init__(self, connection_string: str):
        from azure.storage.blob import BlobServiceClient
        self.connection_string = connection_string
        self.client = BlobServiceClient.from_connection_string(connection_string)
    
    def upload_blob(self, container_name: str, blob_name: str, data: bytes, overwrite: bool = True):
        """Upload data to Azure Blob Storage"""
        blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.upload_blob(data, overwrite=overwrite)
    
    def download_blob(self, container_name: str, blob_name: str) -> bytes:
        """Download data from Azure Blob Storage"""
        blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
        return blob_client.download_blob().readall()
    
    def blob_exists(self, container_name: str, blob_name: str) -> bool:
        """Check if blob exists in Azure"""
        blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
        return blob_client.exists()
    
    def ensure_container(self, container_name: str):
        """Ensure container exists in Azure"""
        container_client = self.client.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()
    
    def generate_upload_url(self, container_name: str, blob_name: str) -> str:
        """Generate SAS URL for uploading"""
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions
        
        sas_token = generate_blob_sas(
            account_name=self.client.account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=self.client.credential.account_key,
            permission=BlobSasPermissions(write=True, create=True),
            expiry=datetime.utcnow() + timedelta(hours=1)
        )
        
        return f"https://{self.client.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"


class LocalFileStorageAdapter(StorageAdapter):
    """Local filesystem implementation for development"""
    
    def __init__(self, base_path: str = "/tmp/speech-flow-storage"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    def _get_blob_path(self, container_name: str, blob_name: str) -> str:
        """Get full file path for a blob"""
        container_path = os.path.join(self.base_path, container_name)
        os.makedirs(container_path, exist_ok=True)
        return os.path.join(container_path, blob_name)
    
    def upload_blob(self, container_name: str, blob_name: str, data: bytes, overwrite: bool = True):
        """Upload data to local filesystem"""
        blob_path = self._get_blob_path(container_name, blob_name)
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(blob_path), exist_ok=True)
        
        # Write file
        mode = 'wb' if overwrite else 'xb'
        with open(blob_path, mode) as f:
            f.write(data)
    
    def download_blob(self, container_name: str, blob_name: str) -> bytes:
        """Download data from local filesystem"""
        blob_path = self._get_blob_path(container_name, blob_name)
        with open(blob_path, 'rb') as f:
            return f.read()
    
    def blob_exists(self, container_name: str, blob_name: str) -> bool:
        """Check if file exists"""
        blob_path = self._get_blob_path(container_name, blob_name)
        return os.path.exists(blob_path)
    
    def ensure_container(self, container_name: str):
        """Ensure directory exists"""
        container_path = os.path.join(self.base_path, container_name)
        os.makedirs(container_path, exist_ok=True)
    
    def generate_upload_url(self, container_name: str, blob_name: str) -> str:
        """Generate file path for uploading (local mode)"""
        blob_path = self._get_blob_path(container_name, blob_name)
        # Create parent directories
        os.makedirs(os.path.dirname(blob_path), exist_ok=True)
        return f"file://{blob_path}"


def get_storage_adapter(connection_string: Optional[str] = None) -> StorageAdapter:
    """
    Factory function to get the appropriate storage adapter based on environment.
    
    Args:
        connection_string: Connection string for Azure Blob Storage.
                          If None, uses AZURE_STORAGE_CONNECTION_STRING env var.
    
    Returns:
        StorageAdapter instance (either Azure Blob Storage or local filesystem)
    """
    environment = os.getenv("ENVIRONMENT", "AZURE").upper()
    
    if environment == "LOCAL":
        # Use local filesystem for local development
        base_path = os.getenv("LOCAL_STORAGE_PATH", "/tmp/speech-flow-storage")
        return LocalFileStorageAdapter(base_path)
    else:
        # Use Azure Blob Storage
        if connection_string is None:
            connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
        return AzureBlobStorageAdapter(connection_string)
