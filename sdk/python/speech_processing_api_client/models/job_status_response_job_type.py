from enum import Enum

class JobStatusResponseJobType(str, Enum):
    LANGUAGE_DETECTION = "language_detection"
    TEXT_TO_SPEECH = "text_to_speech"
    TRANSCRIPTION = "transcription"
    TRANSLATION = "translation"

    def __str__(self) -> str:
        return str(self.value)
