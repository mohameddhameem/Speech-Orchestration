from enum import Enum

class TextToSpeechRequestAudioFormat(str, Enum):
    AAC = "aac"
    MP3 = "mp3"
    OGG = "ogg"
    OPUS = "opus"
    WAV = "wav"

    def __str__(self) -> str:
        return str(self.value)
