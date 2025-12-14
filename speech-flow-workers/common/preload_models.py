#!/usr/bin/env python3
"""
Model Pre-download Script

This script pre-downloads and caches models to a specified directory.
Useful for:
- Pre-loading models into a shared persistent volume
- Validating model downloads before deployment
- Building container images with pre-cached models

Usage:
    python preload_models.py [--all] [--whisper] [--lid] [--cache-dir /path/to/cache]
"""

import argparse
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.model_manager import get_model_manager


def main():
    parser = argparse.ArgumentParser(description="Pre-download and cache models")
    parser.add_argument("--all", action="store_true", help="Download all models")
    parser.add_argument("--whisper", action="store_true", help="Download Whisper model")
    parser.add_argument("--lid", action="store_true", help="Download LID model")
    parser.add_argument("--cache-dir", type=str, help="Cache directory path", default=None)
    parser.add_argument("--clear-cache", action="store_true", help="Clear cache before downloading")
    parser.add_argument("--info", action="store_true", help="Show cache information")

    args = parser.parse_args()

    # Set cache directory if specified
    if args.cache_dir:
        os.environ["MODEL_CACHE_DIR"] = args.cache_dir
        print(f"Using cache directory: {args.cache_dir}")

    # Get model manager instance
    model_manager = get_model_manager()

    # Show cache info if requested
    if args.info:
        print("\n=== Cache Information ===")
        cache_info = model_manager.get_cache_info()
        for key, value in cache_info.items():
            print(f"{key}: {value}")
        print()
        return

    # Clear cache if requested
    if args.clear_cache:
        print("Clearing model cache...")
        model_manager.clear_cache()
        print("Cache cleared.\n")

    # Default to all if no specific model specified
    if not (args.whisper or args.lid):
        args.all = True

    success = True

    # Download Whisper model
    if args.all or args.whisper:
        print("\n=== Downloading Whisper Model ===")
        try:
            model, metadata = model_manager.load_whisper_model()
            if model_manager.validate_whisper_model(model):
                print(f"✓ Whisper model successfully loaded and validated")
                print(f"  Model: {metadata['model_name']}")
                print(f"  Version: {metadata['model_version']}")
                print(f"  Cache: {metadata['cache_dir']}")
            else:
                print("✗ Whisper model validation failed")
                success = False
        except Exception as e:
            print(f"✗ Failed to load Whisper model: {e}")
            success = False

    # Download LID model
    if args.all or args.lid:
        print("\n=== Downloading LID Model ===")
        try:
            processor, model, metadata = model_manager.load_lid_model()
            if model_manager.validate_lid_model(processor, model):
                print(f"✓ LID model successfully loaded and validated")
                print(f"  Model: {metadata['model_name']}")
                print(f"  Version: {metadata['model_version']}")
                print(f"  Cache: {metadata['cache_dir']}")
            else:
                print("✗ LID model validation failed")
                success = False
        except Exception as e:
            print(f"✗ Failed to load LID model: {e}")
            success = False

    # Show final cache info
    print("\n=== Final Cache Information ===")
    cache_info = model_manager.get_cache_info()
    for key, value in cache_info.items():
        print(f"{key}: {value}")

    if success:
        print("\n✓ All models downloaded and validated successfully!")
        return 0
    else:
        print("\n✗ Some models failed to download or validate")
        return 1


if __name__ == "__main__":
    sys.exit(main())
