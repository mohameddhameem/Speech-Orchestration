from enum import Enum

class AudioUploadType(str, Enum):
    MULTIPART_FORM = "multipart_form"

    def __str__(self) -> str:
        return str(self.value)
