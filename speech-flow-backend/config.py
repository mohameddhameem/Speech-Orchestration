import os

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/speechflow")
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;")
    BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME", "raw-audio")
    BLOB_CONTAINER_RESULTS = os.getenv("BLOB_CONTAINER_RESULTS", "results")
    SERVICEBUS_CONNECTION_STRING = os.getenv("SERVICEBUS_CONNECTION_STRING", "Endpoint=sb://localhost/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=SAS_KEY_HERE")
    
    # Centralized Queue Names
    ROUTER_QUEUE_NAME = os.getenv("ROUTER_QUEUE_NAME", "job-events")
    LID_QUEUE_NAME = os.getenv("LID_QUEUE_NAME", "lid-jobs")
    WHISPER_QUEUE_NAME = os.getenv("WHISPER_QUEUE_NAME", "whisper-jobs")
    AZURE_AI_QUEUE_NAME = os.getenv("AZURE_AI_QUEUE_NAME", "azure-ai-jobs")
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://my-resource.openai.azure.com/")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")

settings = Settings()
