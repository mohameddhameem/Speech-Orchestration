from enum import Enum

class AudioBlobReferenceType(str, Enum):
    AZURE_BLOB = "azure_blob"

    def __str__(self) -> str:
        return str(self.value)
