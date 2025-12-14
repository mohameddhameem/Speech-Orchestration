#!/usr/bin/env python3
"""
Quick test script to verify local environment setup
Tests messaging, storage, and AI adapters in LOCAL mode
"""

import json
import os
import sys

# Set to LOCAL mode for testing
os.environ["ENVIRONMENT"] = "LOCAL"
os.environ["RABBITMQ_URL"] = "amqp://guest:guest@localhost:5672/"
os.environ["LOCAL_STORAGE_PATH"] = "/tmp/speech-flow-test-storage"

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "speech-flow-backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "speech-flow-workers"))

print("Testing Local Environment Adapters")
print("=" * 50)

# Test 1: Storage Adapter
print("\n1. Testing Storage Adapter...")
try:
    from speech_flow_backend.storage_adapter import get_storage_adapter

    storage = get_storage_adapter()
    print(f"   ✓ Storage adapter created: {type(storage).__name__}")

    # Test write
    test_data = b'{"test": "data"}'
    storage.ensure_container("test-container")
    storage.upload_blob("test-container", "test.json", test_data)
    print("   ✓ File uploaded successfully")

    # Test read
    retrieved = storage.download_blob("test-container", "test.json")
    assert retrieved == test_data
    print("   ✓ File downloaded successfully")

    # Test exists
    exists = storage.blob_exists("test-container", "test.json")
    assert exists
    print("   ✓ File existence check works")

    print("   ✓ Storage adapter: PASSED")
except Exception as e:
    print(f"   ✗ Storage adapter: FAILED - {e}")
    import traceback

    traceback.print_exc()

# Test 2: AI Adapter
print("\n2. Testing AI Adapter...")
try:
    from speech_flow_workers.common.ai_adapter import get_ai_adapter

    ai = get_ai_adapter()
    print(f"   ✓ AI adapter created: {type(ai).__name__}")

    # Note: We won't actually run inference here as it requires downloading models
    # Just verify the adapter was created successfully
    print("   ✓ AI adapter: PASSED (creation only, inference not tested)")
except Exception as e:
    print(f"   ✗ AI adapter: FAILED - {e}")
    import traceback

    traceback.print_exc()

# Test 3: Config
print("\n3. Testing Configuration...")
try:
    from speech_flow_backend.config import settings

    assert settings.ENVIRONMENT == "LOCAL"
    print(f"   ✓ Environment: {settings.ENVIRONMENT}")
    print(f"   ✓ RabbitMQ URL: {settings.RABBITMQ_URL}")
    print(f"   ✓ Local Storage Path: {settings.LOCAL_STORAGE_PATH}")
    print(f"   ✓ Queue Names: {settings.ROUTER_QUEUE_NAME}, {settings.LID_QUEUE_NAME}")
    print("   ✓ Configuration: PASSED")
except Exception as e:
    print(f"   ✗ Configuration: FAILED - {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 50)
print("Local Environment Test Summary:")
print("All adapter tests completed. See results above.")
print("\nNote: Full integration tests require RabbitMQ and")
print("HuggingFace models to be available.")
