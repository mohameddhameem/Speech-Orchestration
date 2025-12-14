# Model Management Guide

## Overview

The Speech Orchestration system uses a centralized model management approach to handle model downloads, caching, and
loading for all worker services. This guide explains how the system works and how to configure it for your deployment.

## Architecture

### Components

1. **ModelManager** (`common/model_manager.py`)

   - Centralized model download and caching
   - Retry logic with exponential backoff
   - Model validation
   - Cache management utilities

2. **Model Pre-loader** (`common/preload_models.py`)

   - CLI tool for pre-downloading models
   - Useful for container builds and persistent volume initialization

3. **Worker Integration**

   - All workers use the ModelManager for consistent model handling
   - Models loaded once at startup and shared globally within each worker process

## Models Used

### Whisper Model (Transcription)

- **Model**: faster-whisper (CTranslate2 optimized)
- **Default Version**: large-v3
- **Size**: ~3GB
- **Device**: CUDA (GPU) or CPU
- **Cache Location**: `/models/whisper/`

### LID Model (Language Identification)

- **Model**: facebook/mms-lid-126 (Hugging Face)
- **Size**: ~1GB
- **Device**: CPU
- **Cache Location**: `/models/huggingface/hub/`

## Configuration

### Environment Variables

#### Cache Directories

```bash
# Base cache directory (mount as persistent volume in production)
MODEL_CACHE_DIR=/models

# Hugging Face cache (for LID model)
HF_HOME=/models/huggingface
TRANSFORMERS_CACHE=/models/huggingface/hub

# Whisper model cache
WHISPER_CACHE_DIR=/models/whisper
```

#### Model Selection

```bash
# Whisper configuration
WHISPER_MODEL_NAME=large-v3          # Options: tiny, base, small, medium, large, large-v2, large-v3
WHISPER_DEVICE=cuda                   # Options: cuda, cpu
WHISPER_COMPUTE_TYPE=float16          # Options: float16, int8, float32

# LID configuration
LID_MODEL_ID=facebook/mms-lid-126
LID_MODEL_REVISION=main              # Pin to specific commit hash for reproducibility
```

#### Download Retry Configuration

```bash
# Maximum number of download retry attempts
MODEL_DOWNLOAD_MAX_RETRIES=3

# Initial retry delay in seconds (uses exponential backoff)
MODEL_DOWNLOAD_RETRY_DELAY=5
```

## Deployment Strategies

### Strategy 1: Runtime Download (Default)

**Pros**: Smallest container image size **Cons**: Slower first startup, network dependency

```yaml
# No special configuration needed
# Models download on first run and cache in ephemeral storage
# Suitable for development and testing
```

### Strategy 2: Persistent Volume Cache (Recommended for Production)

**Pros**: Fast startup after initial download, shared across pods **Cons**: Requires persistent volume setup

#### Step 1: Create Persistent Volume

```yaml
# pvc-models.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: speech-flow-models
  namespace: speech-flow
spec:
  accessModes:
    - ReadWriteMany  # Required for sharing across multiple pods
  resources:
    requests:
      storage: 10Gi
  storageClassName: azurefile  # Use appropriate storage class
```

#### Step 2: Pre-download Models (One-time Job)

```yaml
# job-preload-models.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: preload-models
  namespace: speech-flow
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: preloader
        image: your-registry/speech-flow-workers:latest
        command: ["python", "common/preload_models.py", "--all"]
        env:
        - name: MODEL_CACHE_DIR
          value: "/models"
        volumeMounts:
        - name: models
          mountPath: /models
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: speech-flow-models
```

Deploy:

```bash
kubectl apply -f pvc-models.yaml
kubectl apply -f job-preload-models.yaml

# Monitor job
kubectl logs -f job/preload-models -n speech-flow
```

#### Step 3: Update Worker Deployments

```yaml
# Add to whisper-worker.yaml and lid-worker.yaml
spec:
  template:
    spec:
      containers:
      - name: worker
        env:
        - name: MODEL_CACHE_DIR
          value: "/models"
        volumeMounts:
        - name: models
          mountPath: /models
          readOnly: true  # Workers only need read access
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: speech-flow-models
```

### Strategy 3: Pre-built Container Images

**Pros**: Fastest startup, no external dependencies **Cons**: Large image size (~5-10GB), longer build times

#### Build with Pre-loaded Models

```bash
cd speech-flow-workers

# Build with models included
docker build \
  --build-arg PRELOAD_MODELS=true \
  -t your-registry/speech-flow-workers:with-models \
  .

# Push to registry
docker push your-registry/speech-flow-workers:with-models
```

**Note**: Uncomment the model pre-download section in the Dockerfile first.

### Strategy 4: Hybrid Approach (Recommended)

Combine persistent volumes with version-specific images:

- Use persistent volumes for model caching
- Pin model versions in environment variables
- Pre-download models to PV for critical workloads
- Allow fallback to runtime download if needed

## Usage Examples

### Pre-download All Models

```bash
python common/preload_models.py --all
```

### Pre-download Specific Model

```bash
# Only Whisper
python common/preload_models.py --whisper

# Only LID
python common/preload_models.py --lid
```

### Use Custom Cache Directory

```bash
python common/preload_models.py --all --cache-dir /custom/path
```

### Clear and Re-download

```bash
python common/preload_models.py --all --clear-cache
```

### Check Cache Information

```bash
python common/preload_models.py --info
```

## Monitoring and Troubleshooting

### Check Model Cache Size

```python
from common.model_manager import get_model_manager

mm = get_model_manager()
info = mm.get_cache_info()
print(info)
```

### Common Issues

#### Issue: Models downloading repeatedly

**Solution**: Ensure cache directory is persistent (not ephemeral container storage)

```bash
# Check if volume is mounted
kubectl exec -it pod-name -- df -h /models

# Verify cache directory permissions
kubectl exec -it pod-name -- ls -la /models
```

#### Issue: Out of disk space

**Solution**: Increase PVC size or use smaller models

```bash
# Check disk usage
kubectl exec -it pod-name -- du -sh /models/*

# Consider using smaller Whisper model
# Set WHISPER_MODEL_NAME=medium or small
```

#### Issue: Download failures

**Solution**: Check network connectivity and retry configuration

```bash
# Increase retries
MODEL_DOWNLOAD_MAX_RETRIES=5
MODEL_DOWNLOAD_RETRY_DELAY=10

# Check logs for specific errors
kubectl logs -f pod-name -n speech-flow
```

#### Issue: GPU out of memory

**Solution**: Use lower precision or smaller model

```bash
# Use int8 quantization
WHISPER_COMPUTE_TYPE=int8

# Or use smaller model
WHISPER_MODEL_NAME=medium
```

## Model Version Pinning

For reproducible deployments, pin model versions:

```bash
# Pin Whisper to specific version (use model name as version identifier)
WHISPER_MODEL_NAME=large-v3

# Pin LID model to specific Hugging Face commit
LID_MODEL_REVISION=abc123def456  # Replace with actual commit hash
```

To find the commit hash:

```bash
# Visit: https://huggingface.co/facebook/mms-lid-126/commits/main
# Copy the commit hash you want to pin to
```

## Performance Optimization

### Reduce Startup Time

1. Use persistent volume cache
2. Pre-download models during deployment
3. Use container images with pre-loaded models

### Reduce Memory Usage

1. Use smaller Whisper models (medium, small, base)
2. Use int8 quantization: `WHISPER_COMPUTE_TYPE=int8`
3. Don't load models you don't need

### Reduce Disk Usage

1. Share persistent volume across all pods
2. Use only required models
3. Clear unused model versions

## Best Practices

1. **Use Persistent Volumes in Production**

   - Ensures fast, consistent startup times
   - Reduces network traffic and external dependencies

2. **Pin Model Versions**

   - Ensures reproducible results
   - Prevents unexpected behavior from model updates

3. **Monitor Cache Usage**

   - Set up alerts for disk space
   - Regularly check cache size and clean up if needed

4. **Implement Health Checks**

   - Verify models loaded successfully at startup
   - Use validation methods from ModelManager

5. **Test Before Deploying**

   - Use preload script to validate models
   - Test with your specific configuration

6. **Document Your Configuration**

   - Keep track of model versions used
   - Document any custom configurations

## Migration Guide

### Migrating from Old Approach

If you're upgrading from the previous model handling approach:

1. **No code changes required** - Workers automatically use ModelManager
2. **Add environment variables** for cache configuration
3. **Set up persistent volumes** (optional but recommended)
4. **Run pre-download job** to populate cache
5. **Update deployments** to mount persistent volumes
6. **Test** with a single pod before rolling out

### Rollback Plan

If you need to rollback:

1. Remove volume mounts from worker deployments
2. Workers will fall back to default behavior
3. Models will download to ephemeral storage

## Support and Troubleshooting

For issues or questions:

1. Check pod logs: `kubectl logs -f pod-name`
2. Verify cache directory exists and is writable
3. Check network connectivity for downloads
4. Review environment variable configuration
5. Use preload script for debugging: `python common/preload_models.py --info`
