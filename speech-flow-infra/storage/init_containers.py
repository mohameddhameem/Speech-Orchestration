import os

from azure.storage.blob import BlobServiceClient

conn = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
svc = BlobServiceClient.from_connection_string(conn)
for name in ["raw-audio", "results"]:
    try:
        svc.create_container(name)
        print(f"Created container: {name}")
    except Exception:
        print(f"Container exists: {name}")
