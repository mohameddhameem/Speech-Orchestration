"""Configuration settings for Speech Orchestration system.

This module provides environment-based configuration for both LOCAL and AZURE modes.
Uses DefaultAzureCredential for Azure services (supports Client Secret, UAMI, SAMI).
"""

import os
from typing import Final


class Settings:
    """Application settings loaded from environment variables."""
    
    # Environment mode: LOCAL or AZURE
    ENVIRONMENT: Final[str] = os.getenv("ENVIRONMENT", "AZURE").upper()
    
    # Database Configuration
    DATABASE_URL: Final[str] = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost/speechflow"
    )
    
    # Azure Storage Configuration (for AZURE mode with DefaultAzureCredential)
    AZURE_STORAGE_ACCOUNT_NAME: Final[str] = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
    AZURE_STORAGE_ACCOUNT_URL: Final[str] = os.getenv(
        "AZURE_STORAGE_ACCOUNT_URL",
        f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME', 'devstoreaccount1')}.blob.core.windows.net"
    )
    
    # Legacy connection string support (for local development with Azurite)
    # NOTE: Only used for local Azurite development. Production uses DefaultAzureCredential.
    AZURE_STORAGE_CONNECTION_STRING: Final[str] = os.getenv(
        "AZURE_STORAGE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
        "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
    )
    
    # Local Storage Configuration (for LOCAL mode)
    LOCAL_STORAGE_PATH: Final[str] = os.getenv("LOCAL_STORAGE_PATH", "/tmp/speech-flow-storage")
    
    # Blob Container Names
    BLOB_CONTAINER_NAME: Final[str] = os.getenv("BLOB_CONTAINER_NAME", "raw-audio")
    BLOB_CONTAINER_RESULTS: Final[str] = os.getenv("BLOB_CONTAINER_RESULTS", "results")
    
    # Azure Service Bus Configuration (for AZURE mode with DefaultAzureCredential)
    SERVICEBUS_NAMESPACE: Final[str] = os.getenv("SERVICEBUS_NAMESPACE", "")
    SERVICEBUS_FQDN: Final[str] = os.getenv(
        "SERVICEBUS_FQDN",
        f"{os.getenv('SERVICEBUS_NAMESPACE', 'localhost')}.servicebus.windows.net"
    )
    
    # Legacy connection string support (for backward compatibility)
    # NOTE: Only used when DefaultAzureCredential is not available
    SERVICEBUS_CONNECTION_STRING: Final[str] = os.getenv(
        "SERVICEBUS_CONNECTION_STRING",
        "Endpoint=sb://localhost/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=SAS_KEY_HERE"
    )
    
    # RabbitMQ Configuration (for LOCAL mode)
    RABBITMQ_URL: Final[str] = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    # Queue Names (used in both LOCAL and AZURE modes)
    ROUTER_QUEUE_NAME: Final[str] = os.getenv("ROUTER_QUEUE_NAME", "job-events")
    LID_QUEUE_NAME: Final[str] = os.getenv("LID_QUEUE_NAME", "lid-jobs")
    WHISPER_QUEUE_NAME: Final[str] = os.getenv("WHISPER_QUEUE_NAME", "whisper-jobs")
    AZURE_AI_QUEUE_NAME: Final[str] = os.getenv("AZURE_AI_QUEUE_NAME", "azure-ai-jobs")
    
    # Azure OpenAI Configuration (for AZURE mode)
    AZURE_OPENAI_ENDPOINT: Final[str] = os.getenv(
        "AZURE_OPENAI_ENDPOINT",
        "https://my-resource.openai.azure.com/"
    )
    AZURE_OPENAI_DEPLOYMENT: Final[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    
    # Legacy API key support (DefaultAzureCredential preferred)
    AZURE_OPENAI_KEY: Final[str] = os.getenv("AZURE_OPENAI_KEY", "")
    
    # HuggingFace Models (for LOCAL mode)
    HF_SUMMARIZATION_MODEL: Final[str] = os.getenv(
        "HF_SUMMARIZATION_MODEL",
        "facebook/bart-large-cnn"
    )
    HF_TRANSLATION_MODEL: Final[str] = os.getenv(
        "HF_TRANSLATION_MODEL",
        "Helsinki-NLP/opus-mt-{src}-{tgt}"
    )
    
    @property
    def is_local_mode(self) -> bool:
        """Check if running in LOCAL mode."""
        return self.ENVIRONMENT == "LOCAL"
    
    @property
    def is_azure_mode(self) -> bool:
        """Check if running in AZURE mode."""
        return self.ENVIRONMENT == "AZURE"


settings = Settings()
