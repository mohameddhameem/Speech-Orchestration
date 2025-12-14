import asyncio
import os
import sys
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base_worker import BaseWorker, StepMetrics
from common.model_manager import get_model_manager

# Load Model (Global to avoid reloading)
print("Loading Whisper V3 Large Model...")
model_manager = get_model_manager()
model, model_metadata = model_manager.load_whisper_model()

# Validate model loaded correctly
if not model_manager.validate_whisper_model(model):
    raise RuntimeError("Whisper model validation failed")

MODEL_NAME = model_metadata["model_name"]
MODEL_VERSION = model_metadata["model_version"]
DEVICE = model_metadata["device"]
COMPUTE_TYPE = model_metadata["compute_type"]
print(f"Model Loaded. Device: {DEVICE}, Compute: {COMPUTE_TYPE}")


class WhisperWorker(BaseWorker):
    """Transcription Worker using faster-whisper on GPU"""

    def __init__(self):
        queue_name = os.getenv("WHISPER_QUEUE_NAME", "whisper-jobs")
        super().__init__(queue_name=queue_name, step_name="TRANSCRIBE")

    def transcribe(self, audio_path: str, language: str) -> tuple:
        """
        Transcribe audio file.
        Returns: (text, segments_list, audio_duration, word_count, char_count)
        """
        segments, info = model.transcribe(audio_path, language=language, beam_size=5)

        transcript_text = ""
        segments_list = []

        for segment in segments:
            transcript_text += segment.text + " "
            segments_list.append({"start": segment.start, "end": segment.end, "text": segment.text})

        transcript_text = transcript_text.strip()
        word_count = len(transcript_text.split()) if transcript_text else 0
        char_count = len(transcript_text)
        audio_duration = info.duration if info else 0

        return transcript_text, segments_list, audio_duration, word_count, char_count

    async def process(self, job_id: str, payload: dict, metrics: StepMetrics, sb_client) -> dict:
        """Process transcription task with metrics collection"""
        language = payload.get("language", "en")
        local_filename = f"/tmp/{job_id}.wav"

        # Record model info
        # Note: MODEL_NAME from model_metadata already includes 'whisper-' prefix
        # e.g., "whisper-large-v3" not just "large-v3"
        metrics.model_name = MODEL_NAME
        metrics.model_version = MODEL_VERSION

        try:
            # Download audio
            self.download_audio(f"{job_id}.wav", local_filename)

            # Run transcription with timing for RTF calculation
            transcribe_start = time.perf_counter()
            text, segments, audio_duration, word_count, char_count = self.transcribe(local_filename, language)
            transcribe_time = time.perf_counter() - transcribe_start

            # Calculate Real-Time Factor (RTF = processing_time / audio_duration)
            # RTF < 1.0 means faster than real-time
            rtf = transcribe_time / audio_duration if audio_duration > 0 else 0

            # Record transcription metrics
            metrics.audio_duration_seconds = round(audio_duration, 2)
            metrics.transcript_word_count = word_count
            metrics.transcript_char_count = char_count
            metrics.transcription_rtf = round(rtf, 3)

            print(f"[WHISPER] Transcription complete. {word_count} words, {char_count} chars, RTF: {rtf:.3f}")

            # Save full result to blob
            result_data = {
                "job_id": job_id,
                "text": text,
                "segments": segments,
                "language": language,
                "audio_duration_seconds": round(audio_duration, 2),
                "word_count": word_count,
                "char_count": char_count,
                "rtf": round(rtf, 3),
            }
            blob_path = self.upload_result(job_id, "transcript", result_data)

            return {
                "blob_path": blob_path,
                "text_preview": text[:200] + "..." if len(text) > 200 else text,
                "word_count": word_count,
                "rtf": round(rtf, 3),
            }
        except Exception as e:
            metrics.error_code = "TRANSCRIPTION_ERROR"
            raise
        finally:
            if os.path.exists(local_filename):
                os.remove(local_filename)


if __name__ == "__main__":
    worker = WhisperWorker()
    asyncio.run(worker.run())
