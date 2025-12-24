from enum import Enum

class TranscribeAudioFilesBodyOutputFormat(str, Enum):
    JSON = "json"
    PLAIN_TEXT = "plain_text"
    SRT = "srt"
    VTT = "vtt"

    def __str__(self) -> str:
        return str(self.value)
