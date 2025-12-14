"""
Model Manager Module

This module provides centralized model management for all workers including:
- Configurable model download and caching
- Model version pinning
- Download retry logic with exponential backoff
- Model validation
- Persistent cache support for containerized environments
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelConfig:
    """Configuration for model downloads and caching"""

    # Base cache directory - can be mounted as persistent volume in Kubernetes
    DEFAULT_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "/models")

    # Hugging Face cache configuration
    HF_HOME = os.getenv("HF_HOME", os.path.join(DEFAULT_CACHE_DIR, "huggingface"))
    TRANSFORMERS_CACHE = os.getenv("TRANSFORMERS_CACHE", os.path.join(HF_HOME, "hub"))

    # Whisper model cache
    WHISPER_CACHE_DIR = os.getenv("WHISPER_CACHE_DIR", os.path.join(DEFAULT_CACHE_DIR, "whisper"))

    # Download retry configuration
    MAX_RETRIES = int(os.getenv("MODEL_DOWNLOAD_MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("MODEL_DOWNLOAD_RETRY_DELAY", "5"))  # seconds

    # Model version configuration
    WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "large-v3")
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cuda")
    WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16")

    LID_MODEL_ID = os.getenv("LID_MODEL_ID", "facebook/mms-lid-126")
    LID_MODEL_REVISION = os.getenv("LID_MODEL_REVISION", "main")  # Pin to specific commit/tag

    @classmethod
    def setup_cache_dirs(cls):
        """Ensure all cache directories exist"""
        for directory in [cls.DEFAULT_CACHE_DIR, cls.HF_HOME, cls.TRANSFORMERS_CACHE, cls.WHISPER_CACHE_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache directory ready: {directory}")


class ModelManager:
    """
    Centralized model manager for downloading, caching, and loading models.
    Supports retry logic, validation, and persistent caching.
    """

    def __init__(self):
        self.config = ModelConfig()
        self.config.setup_cache_dirs()
        self._setup_environment()

    def _setup_environment(self):
        """Set environment variables for model caching"""
        os.environ["HF_HOME"] = self.config.HF_HOME
        os.environ["TRANSFORMERS_CACHE"] = self.config.TRANSFORMERS_CACHE
        os.environ["TORCH_HOME"] = self.config.DEFAULT_CACHE_DIR
        logger.info(f"Model cache environment configured:")
        logger.info(f"  HF_HOME: {self.config.HF_HOME}")
        logger.info(f"  TRANSFORMERS_CACHE: {self.config.TRANSFORMERS_CACHE}")
        logger.info(f"  WHISPER_CACHE_DIR: {self.config.WHISPER_CACHE_DIR}")

    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with retry logic and exponential backoff"""
        for attempt in range(1, self.config.MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.config.MAX_RETRIES:
                    logger.error(f"Failed after {attempt} attempts: {e}")
                    raise

                wait_time = self.config.RETRY_DELAY * (2 ** (attempt - 1))
                logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

    def load_whisper_model(self) -> Tuple[Any, dict]:
        """
        Load Whisper model with caching and retry logic.

        Returns:
            Tuple of (model, metadata_dict)
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError("faster-whisper is not installed. Run: pip install faster-whisper")

        logger.info(f"Loading Whisper model: {self.config.WHISPER_MODEL_NAME}")
        logger.info(f"Device: {self.config.WHISPER_DEVICE}, Compute Type: {self.config.WHISPER_COMPUTE_TYPE}")

        def _load():
            return WhisperModel(
                self.config.WHISPER_MODEL_NAME,
                device=self.config.WHISPER_DEVICE,
                compute_type=self.config.WHISPER_COMPUTE_TYPE,
                download_root=self.config.WHISPER_CACHE_DIR,
            )

        model = self._retry_with_backoff(_load)

        metadata = {
            "model_name": f"whisper-{self.config.WHISPER_MODEL_NAME}",
            "model_version": "faster-whisper-0.10.0",
            "device": self.config.WHISPER_DEVICE,
            "compute_type": self.config.WHISPER_COMPUTE_TYPE,
            "cache_dir": self.config.WHISPER_CACHE_DIR,
        }

        logger.info(f"✓ Whisper model loaded successfully")
        return model, metadata

    def load_lid_model(self) -> Tuple[Any, Any, dict]:
        """
        Load Language Identification model with caching and retry logic.

        Returns:
            Tuple of (processor, model, metadata_dict)
        """
        try:
            from transformers import AutoFeatureExtractor, Wav2Vec2ForSequenceClassification
        except ImportError:
            raise ImportError("transformers is not installed. Run: pip install transformers")

        logger.info(f"Loading LID model: {self.config.LID_MODEL_ID}")

        def _load_processor():
            return AutoFeatureExtractor.from_pretrained(
                self.config.LID_MODEL_ID,
                revision=self.config.LID_MODEL_REVISION,
                cache_dir=self.config.TRANSFORMERS_CACHE,
            )

        def _load_model():
            return Wav2Vec2ForSequenceClassification.from_pretrained(
                self.config.LID_MODEL_ID,
                revision=self.config.LID_MODEL_REVISION,
                cache_dir=self.config.TRANSFORMERS_CACHE,
            )

        processor = self._retry_with_backoff(_load_processor)
        model = self._retry_with_backoff(_load_model)

        metadata = {
            "model_name": self.config.LID_MODEL_ID,
            "model_version": self.config.LID_MODEL_REVISION,
            "cache_dir": self.config.TRANSFORMERS_CACHE,
        }

        logger.info(f"✓ LID model loaded successfully")
        return processor, model, metadata

    def validate_whisper_model(self, model) -> bool:
        """
        Validate that Whisper model is loaded correctly.

        Args:
            model: WhisperModel instance

        Returns:
            True if model is valid, False otherwise
        """
        try:
            # Check if model has expected attributes
            if not hasattr(model, "transcribe"):
                logger.error("Whisper model missing 'transcribe' method")
                return False
            logger.info("✓ Whisper model validation passed")
            return True
        except Exception as e:
            logger.error(f"Whisper model validation failed: {e}")
            return False

    def validate_lid_model(self, processor, model) -> bool:
        """
        Validate that LID model components are loaded correctly.

        Args:
            processor: AutoFeatureExtractor instance
            model: Wav2Vec2ForSequenceClassification instance

        Returns:
            True if models are valid, False otherwise
        """
        try:
            # Check processor
            if not hasattr(processor, "__call__"):
                logger.error("LID processor missing __call__ method")
                return False

            # Check model
            if not hasattr(model, "config") or not hasattr(model.config, "id2label"):
                logger.error("LID model missing expected config")
                return False

            logger.info("✓ LID model validation passed")
            return True
        except Exception as e:
            logger.error(f"LID model validation failed: {e}")
            return False

    def get_cache_info(self) -> dict:
        """
        Get information about model cache usage.

        Returns:
            Dictionary with cache statistics
        """

        def get_dir_size(path):
            """Calculate total size of directory"""
            total = 0
            try:
                for entry in Path(path).rglob("*"):
                    if entry.is_file():
                        total += entry.stat().st_size
            except Exception as e:
                logger.warning(f"Error calculating size for {path}: {e}")
            return total

        cache_info = {
            "cache_root": self.config.DEFAULT_CACHE_DIR,
            "hf_cache": self.config.HF_HOME,
            "whisper_cache": self.config.WHISPER_CACHE_DIR,
            "hf_cache_size_mb": round(get_dir_size(self.config.HF_HOME) / 1024 / 1024, 2),
            "whisper_cache_size_mb": round(get_dir_size(self.config.WHISPER_CACHE_DIR) / 1024 / 1024, 2),
        }

        return cache_info

    def clear_cache(self, model_type: Optional[str] = None):
        """
        Clear model cache.

        Args:
            model_type: Type of model cache to clear ('whisper', 'lid', or None for all)
        """
        import shutil

        if model_type == "whisper" or model_type is None:
            if Path(self.config.WHISPER_CACHE_DIR).exists():
                shutil.rmtree(self.config.WHISPER_CACHE_DIR)
                self.config.setup_cache_dirs()
                logger.info("Whisper cache cleared")

        if model_type == "lid" or model_type is None:
            if Path(self.config.TRANSFORMERS_CACHE).exists():
                shutil.rmtree(self.config.TRANSFORMERS_CACHE)
                self.config.setup_cache_dirs()
                logger.info("LID cache cleared")


# Singleton instance
_model_manager = None


def get_model_manager() -> ModelManager:
    """Get or create the global ModelManager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
