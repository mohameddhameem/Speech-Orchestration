from enum import Enum

class TranscriptionRequestConfigModel(str, Enum):
    AZURE_SPEECH_STANDARD = "azure-speech-standard"
    WHISPER_LARGE_V3 = "whisper-large-v3"

    def __str__(self) -> str:
        return str(self.value)
