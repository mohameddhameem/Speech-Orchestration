# Speech Orchestration Pipeline

Event-driven speech processing system supporting both local development and Azure cloud deployment.

## Quick Start (Local)

```bash
# Start all services locally
docker-compose -f docker-compose.yaml -f docker-compose.local.yml up -d

# Access services
# API: http://localhost:8000/docs
# Upload UI: http://localhost:8502
# Operations Dashboard: http://localhost:8501
# RabbitMQ: http://localhost:15672 (guest/guest)
```

## Documentation

- **[Local Development Guide](LOCAL_DEVELOPMENT.md)**: Detailed instructions for running and testing locally.
- **[Hybrid Development Guide](HYBRID_DEVELOPMENT.md)**: Run locally with real Azure resources (Service Bus, Blob Storage).
- **[Azure Implementation Guide](IMPLEMENTATION_GUIDE.md)**: Complete guide for deploying to Azure Kubernetes Service (AKS).
- **[Architecture & Design](ARCHITECTURE.md)**: Internal software architecture, data models, and workflows.
- **[Model Management](speech-flow-workers/MODEL_MANAGEMENT.md)**: How to manage, cache, and update ML models.
- **[Docker Security](DOCKER_SECURITY.md)**: Security optimizations and best practices.

## Project Structure

```
speech-flow-backend/    # API, Router, Dashboard
speech-flow-ui/         # Self-service Upload UI
speech-flow-workers/    # AI Workers (LID, Whisper, Azure AI)
speech-flow-infra/      # Infrastructure (K8s, Terraform, DB)
```

## License

[Add your license here]

