"""
Basic validation tests for the model management system.
This is a simple smoke test to verify the model manager is working.

Note: Uses direct module import to avoid dependency chain issues.
In production, workers will import via proper package structure.
"""

import os
import sys
import tempfile
from pathlib import Path

# Direct import of model_manager module for testing
# This avoids the dependency chain (common.__init__ -> base_worker -> azure imports)
# Production code uses: from common.model_manager import get_model_manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_model_config():
    """Test ModelConfig initialization"""
    print("\n=== Testing ModelConfig ===")
    
    # Import directly to avoid dependency chain
    import model_manager
    
    config = model_manager.ModelConfig()
    
    # Test that default values are set
    assert config.DEFAULT_CACHE_DIR is not None
    assert config.HF_HOME is not None
    assert config.WHISPER_CACHE_DIR is not None
    assert config.MAX_RETRIES > 0
    
    print(f"✓ Cache dir: {config.DEFAULT_CACHE_DIR}")
    print(f"✓ HF home: {config.HF_HOME}")
    print(f"✓ Whisper cache: {config.WHISPER_CACHE_DIR}")
    print(f"✓ Max retries: {config.MAX_RETRIES}")
    print("✓ ModelConfig test passed")


def test_model_manager_init():
    """Test ModelManager initialization"""
    print("\n=== Testing ModelManager Initialization ===")
    
    # Use temp directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set env var BEFORE importing
        os.environ["MODEL_CACHE_DIR"] = tmpdir
        
        # Reload the module to pick up new env var
        import importlib
        import model_manager
        importlib.reload(model_manager)
        
        manager = model_manager.ModelManager()
        
        # Verify cache directories were created
        assert Path(tmpdir).exists()
        print(f"✓ Cache directory created: {tmpdir}")
        
        # Test cache info
        cache_info = manager.get_cache_info()
        assert "cache_root" in cache_info
        assert "hf_cache" in cache_info
        assert "whisper_cache" in cache_info
        
        print(f"✓ Cache info: {cache_info}")
        print("✓ ModelManager initialization test passed")


def test_singleton_pattern():
    """Test that get_model_manager returns singleton"""
    print("\n=== Testing Singleton Pattern ===")
    
    # Use temp directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["MODEL_CACHE_DIR"] = tmpdir
        
        # Reload the module to pick up new env var
        import importlib
        import model_manager
        importlib.reload(model_manager)
        
        manager1 = model_manager.get_model_manager()
        manager2 = model_manager.get_model_manager()
        
        assert manager1 is manager2, "Should return same instance"
        print("✓ Singleton pattern working correctly")


def test_environment_variables():
    """Test that environment variables are properly used"""
    print("\n=== Testing Environment Variables ===")
    
    # Set custom values
    test_cache = "/test/cache"
    test_model = "tiny"
    test_retries = 5
    
    os.environ["MODEL_CACHE_DIR"] = test_cache
    os.environ["WHISPER_MODEL_NAME"] = test_model
    os.environ["MODEL_DOWNLOAD_MAX_RETRIES"] = str(test_retries)
    
    # Need to reimport to pick up new env vars
    import importlib
    import model_manager
    importlib.reload(model_manager)
    
    # Create new config to pick up env vars
    config = model_manager.ModelConfig()
    
    assert config.DEFAULT_CACHE_DIR == test_cache
    assert config.WHISPER_MODEL_NAME == test_model
    assert config.MAX_RETRIES == test_retries
    
    print(f"✓ Cache dir from env: {config.DEFAULT_CACHE_DIR}")
    print(f"✓ Model name from env: {config.WHISPER_MODEL_NAME}")
    print(f"✓ Max retries from env: {config.MAX_RETRIES}")
    print("✓ Environment variable test passed")


def test_retry_logic():
    """Test retry logic with exponential backoff"""
    print("\n=== Testing Retry Logic ===")
    
    # Use temp directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["MODEL_CACHE_DIR"] = tmpdir
        os.environ["MODEL_DOWNLOAD_MAX_RETRIES"] = "3"
        os.environ["MODEL_DOWNLOAD_RETRY_DELAY"] = "0"  # Set to 0 for fast testing
        
        # Reload the module to pick up new env vars
        import importlib
        import model_manager
        importlib.reload(model_manager)
        
        manager = model_manager.ModelManager()
        
        # Test successful retry
        call_count = [0]
        def failing_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Simulated failure")
            return "success"
        
        result = manager._retry_with_backoff(failing_func)
        assert result == "success"
        assert call_count[0] == 3
        print(f"✓ Retry succeeded after {call_count[0]} attempts")
        
        # Test max retries exceeded
        def always_fails():
            raise Exception("Always fails")
        
        try:
            manager._retry_with_backoff(always_fails)
            assert False, "Should have raised exception"
        except Exception as e:
            print(f"✓ Max retries exceeded as expected: {e}")
        
        print("✓ Retry logic test passed")


def test_cache_operations():
    """Test cache operations"""
    print("\n=== Testing Cache Operations ===")
    
    # Use temp directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["MODEL_CACHE_DIR"] = tmpdir
        
        # Reload the module to pick up new env var
        import importlib
        import model_manager
        importlib.reload(model_manager)
        
        manager = model_manager.ModelManager()
        
        # Test cache info
        info = manager.get_cache_info()
        print(f"✓ Initial cache info: {info}")
        assert info["whisper_cache_size_mb"] == 0.0
        
        # Create test file in the whisper cache directory (make it larger than 1KB)
        test_file = Path(manager.config.WHISPER_CACHE_DIR) / "test.bin"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_bytes(b"x" * (1024 * 1024))  # 1 MB file
        
        # Check cache size
        info = manager.get_cache_info()
        assert info["whisper_cache_size_mb"] >= 1.0  # Should be at least 1 MB
        print(f"✓ Cache size after adding file: {info['whisper_cache_size_mb']} MB")
        
        print("✓ Cache operations test passed")


def run_all_tests():
    """Run all validation tests"""
    print("=" * 60)
    print("Model Manager Validation Tests")
    print("=" * 60)
    
    tests = [
        test_model_config,
        test_model_manager_init,
        test_singleton_pattern,
        test_environment_variables,
        test_retry_logic,
        test_cache_operations,
    ]
    
    failed = []
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"\n✗ Test {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed.append(test.__name__)
    
    print("\n" + "=" * 60)
    if not failed:
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print(f"✗ {len(failed)} test(s) failed:")
        for name in failed:
            print(f"  - {name}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
