# Quick Start Guide: Model Management Deployment

This guide walks you through deploying the Speech Orchestration system with the new model management features.

## Prerequisites

- Kubernetes cluster with appropriate storage class (Azure Files, NFS, etc.)
- kubectl configured to access your cluster
- Container images built and pushed to registry

## Option 1: Quick Deployment (Runtime Download)

This is the fastest way to get started. Models download on first pod startup.

### Step 1: Build and Deploy

```bash
# Build and push images
cd speech-flow-workers
docker build -t your-registry/speech-flow-workers:latest .
docker push your-registry/speech-flow-workers:latest

# Deploy workers (no changes needed from original deployment)
kubectl apply -f speech-flow-infra/k8s/
```

**Note**: First startup will be slower as models download. Subsequent restarts will also be slow if pods are
rescheduled.

## Option 2: Production Deployment (Persistent Cache)

Recommended for production. Models are pre-downloaded to a shared persistent volume.

### Step 1: Create Persistent Volume

```bash
# Edit storage class if needed
vi speech-flow-infra/k8s/08-model-cache.yaml

# Create PVC
kubectl apply -f speech-flow-infra/k8s/08-model-cache.yaml
```

### Step 2: Pre-download Models

```bash
# Update image references in 08-model-cache.yaml
sed -i 's/${CONTAINER_REGISTRY}/your-registry/g' speech-flow-infra/k8s/08-model-cache.yaml
sed -i 's/${IMAGE_TAG}/latest/g' speech-flow-infra/k8s/08-model-cache.yaml

# Create pre-load job
kubectl apply -f speech-flow-infra/k8s/08-model-cache.yaml

# Monitor the job
kubectl logs -f job/preload-models -n speech-flow

# Wait for job to complete
kubectl wait --for=condition=complete job/preload-models -n speech-flow --timeout=600s
```

### Step 3: Update Worker Deployments

Add the following to your worker deployment YAML files:

```yaml
spec:
  template:
    spec:
      containers:
      - name: worker
        env:
        # Add model cache configuration
        - name: MODEL_CACHE_DIR
          value: "/models"
        - name: MODEL_DOWNLOAD_MAX_RETRIES
          value: "3"
        volumeMounts:
        - name: models
          mountPath: /models
          readOnly: true
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: speech-flow-models
```

Or use the provided example:

```bash
# Use as reference to update your existing deployments
cat speech-flow-infra/k8s/09-worker-deployment-example.yaml
```

### Step 4: Deploy Workers

```bash
# Deploy updated workers
kubectl apply -f your-worker-deployments.yaml

# Verify pods are running
kubectl get pods -n speech-flow -w
```

## Option 3: Pre-built Images (Fastest Startup)

Models are included in the container image (larger image size).

### Step 1: Build Image with Models

```bash
cd speech-flow-workers

# Uncomment the PRELOAD_MODELS section in Dockerfile
vi Dockerfile

# Build with models
docker build \
  --build-arg PRELOAD_MODELS=true \
  -t your-registry/speech-flow-workers:with-models \
  .

# Push to registry (this will take longer due to large image size)
docker push your-registry/speech-flow-workers:with-models
```

### Step 2: Deploy Workers

```bash
# Update deployments to use the new image tag
kubectl set image deployment/speechflow-whisper-worker \
  whisper-worker=your-registry/speech-flow-workers:with-models \
  -n speech-flow

kubectl set image deployment/speechflow-lid-worker \
  lid-worker=your-registry/speech-flow-workers:with-models \
  -n speech-flow
```

## Verification

### Check Model Cache

```bash
# Exec into a worker pod
kubectl exec -it deployment/speechflow-whisper-worker -n speech-flow -- /bin/bash

# Check cache contents
ls -lh /models/
du -sh /models/*

# Run cache info script
python common/preload_models.py --info
```

### Verify Worker Logs

```bash
# Check Whisper worker logs
kubectl logs -f deployment/speechflow-whisper-worker -n speech-flow

# Look for:
# - "Loading Whisper V3 Large Model..."
# - "Model Loaded. Device: cuda, Compute: float16"
# - "✓ Whisper model loaded successfully"

# Check LID worker logs
kubectl logs -f deployment/speechflow-lid-worker -n speech-flow

# Look for:
# - "Loading MMS LID Model..."
# - "Model Loaded."
# - "✓ LID model loaded successfully"
```

### Test End-to-End

```bash
# Submit a test job through the API
curl -X POST http://your-api-endpoint/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "full_pipeline",
    "audio_filename": "test.wav"
  }'

# Monitor job processing
kubectl logs -f deployment/speechflow-router -n speech-flow
```

## Troubleshooting

### Models Download Every Time

**Problem**: Workers re-download models on each restart

**Solution**: Ensure persistent volume is properly mounted

```bash
# Check volume mounts
kubectl describe pod speechflow-whisper-worker-xxx -n speech-flow | grep -A 5 "Mounts:"

# Verify PVC is bound
kubectl get pvc -n speech-flow

# Check cache directory
kubectl exec -it pod-name -n speech-flow -- df -h /models
```

### Pre-load Job Fails

**Problem**: Model pre-load job fails or times out

**Solution**: Check logs and increase resources/timeout

```bash
# Check job logs
kubectl logs job/preload-models -n speech-flow

# Delete and recreate with more resources
kubectl delete job preload-models -n speech-flow

# Edit 08-model-cache.yaml to increase memory/CPU
# Then reapply
kubectl apply -f speech-flow-infra/k8s/08-model-cache.yaml
```

### Out of Disk Space

**Problem**: PVC runs out of space

**Solution**: Increase PVC size or use smaller models

```bash
# Check current usage
kubectl exec -it pod-name -n speech-flow -- du -sh /models/*

# Resize PVC (if your storage class supports it)
kubectl patch pvc speech-flow-models -n speech-flow \
  -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'

# Or use smaller Whisper model
# Set WHISPER_MODEL_NAME=medium instead of large-v3
```

### Slow Worker Startup

**Problem**: Workers take a long time to start

**Cause**: Models downloading at runtime

**Solution**: Use Option 2 (Persistent Cache) or Option 3 (Pre-built Images)

## Configuration Tips

### Optimize for Your Use Case

**CPU-only deployment**:

```bash
# Set for all workers
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8  # Faster on CPU
```

**Memory-constrained environment**:

```bash
# Use smaller Whisper model
WHISPER_MODEL_NAME=medium  # or small, base, tiny
```

**Multi-region deployment**:

```bash
# Pin model versions for consistency
LID_MODEL_REVISION=abc123  # Use specific commit hash
```

### Monitoring

Add these metrics to your monitoring:

- Model cache disk usage
- Worker startup time
- Model download failures
- Cache hit/miss rates

### Maintenance

Schedule regular cache updates:

```bash
# The CronJob in 08-model-cache.yaml automatically updates models weekly
# Adjust schedule as needed
```

## Next Steps

1. Set up monitoring and alerting for model cache
2. Document your model versions for compliance
3. Test disaster recovery (cache deletion and recreation)
4. Consider setting up a model registry for versioning
5. Implement automated testing of model updates

## Support

For issues or questions:

- Check logs: `kubectl logs -f pod-name -n speech-flow`
- Review documentation: `speech-flow-workers/MODEL_MANAGEMENT.md`
- Run diagnostics: `python common/preload_models.py --info`
