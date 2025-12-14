import os
import sys
import asyncio
import torch
import torchaudio
from transformers import Wav2Vec2ForSequenceClassification, AutoFeatureExtractor

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.base_worker import BaseWorker, StepMetrics

# Load Model (Global to avoid reloading)
print("Loading MMS LID Model...")
MODEL_ID = "facebook/mms-lid-126"
MODEL_VERSION = "1.0"  # Track model version for reproducibility
processor = AutoFeatureExtractor.from_pretrained(MODEL_ID)
model = Wav2Vec2ForSequenceClassification.from_pretrained(MODEL_ID)
print("Model Loaded.")


class LIDWorker(BaseWorker):
    """Language Identification Worker using Facebook MMS model"""
    
    def __init__(self):
        queue_name = os.getenv("LID_QUEUE_NAME", "lid-jobs")
        super().__init__(queue_name=queue_name, step_name="LID")
    
    def identify_language(self, audio_path: str) -> tuple[str, float, float]:
        """
        Run language identification on audio file.
        Returns: (language_code, confidence_score, audio_duration_seconds)
        """
        # Load audio
        waveform, sample_rate = torchaudio.load(audio_path)
        
        # Calculate audio duration
        audio_duration_seconds = waveform.shape[1] / sample_rate
        
        # Resample to 16k if needed
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
            waveform = resampler(waveform)
        
        # Take first 30 seconds for LID
        if waveform.shape[1] > 16000 * 30:
            waveform = waveform[:, :16000 * 30]

        inputs = processor(waveform.squeeze().numpy(), sampling_rate=16000, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            
            # Get prediction and confidence
            probabilities = torch.nn.functional.softmax(logits, dim=-1)
            predicted_id = torch.argmax(logits, dim=-1).item()
            confidence = probabilities[0][predicted_id].item()
            label = model.config.id2label[predicted_id]
        
        return label, confidence, audio_duration_seconds
    
    async def process(self, job_id: str, payload: dict, metrics: StepMetrics, sb_client) -> dict:
        """Process LID task with metrics collection"""
        local_filename = f"/tmp/{job_id}.wav"
        
        # Record model info
        metrics.model_name = MODEL_ID
        metrics.model_version = MODEL_VERSION
        
        try:
            # Download audio
            self.download_audio(f"{job_id}.wav", local_filename)
            
            # Run inference
            lang_code, confidence, audio_duration = self.identify_language(local_filename)
            
            # Record LID-specific metrics
            metrics.detected_language = lang_code
            metrics.language_confidence = round(confidence, 4)
            metrics.audio_duration_seconds = round(audio_duration, 2)
            
            print(f"[LID] Detected Language: {lang_code} (confidence: {confidence:.3f})")
            
            return {
                "language": lang_code,
                "confidence": round(confidence, 4),
                "audio_duration_seconds": round(audio_duration, 2)
            }
        except Exception as e:
            metrics.error_code = "LID_INFERENCE_ERROR"
            raise
        finally:
            if os.path.exists(local_filename):
                os.remove(local_filename)


if __name__ == "__main__":
    worker = LIDWorker()
    asyncio.run(worker.run())
