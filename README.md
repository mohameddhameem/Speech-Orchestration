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

# Speech Processing API Design

This repository contains the complete design, specification, and documentation for a production-grade Speech Processing API.

## Repository Structure

- **`docs/`**: Comprehensive documentation for the API design.
  - [00_Executive_Summary.md](docs/00_Executive_Summary.md): High-level overview of the project scope and outcomes.
  - [01_Design_Overview.md](docs/01_Design_Overview.md): The master design document covering architecture, decisions, and endpoints.
  - [02_Implementation_Guide.md](docs/02_Implementation_Guide.md): Detailed guide for implementers (backend/devops).
  - [03_Authentication_Deep_Dive.md](docs/03_Authentication_Deep_Dive.md): Specifics on the secure `DefaultAzureCredential` implementation.

- **`specs/`**: Machine-readable API specifications.
  - [openapi.yaml](specs/openapi.yaml): OpenAPI 3.1 definition of the API.

- **`examples/`**: Sample code and SDKs.
  - [client_sdk.py](examples/client_sdk.py): A reference Python client SDK implementing the design patterns.

## Getting Started

1. **Review the Design**: Start with the [Executive Summary](docs/00_Executive_Summary.md) and then the [Design Overview](docs/01_Design_Overview.md).
2. **Explore the API**: Open [specs/openapi.yaml](specs/openapi.yaml) in a Swagger editor or VS Code extension to visualize the endpoints.
3. **Understand the Implementation**: Read the [Implementation Guide](docs/02_Implementation_Guide.md) to understand the backend requirements.
4. **Check the Client**: Look at [examples/client_sdk.py](examples/client_sdk.py) to see how a client interacts with the API securely.

## Key Features

- **Async-First**: Job-based architecture for reliability.
- **Hybrid Engine**: Combines self-hosted Whisper V3 (cost) with Azure Speech (quality/coverage).
- **Secure**: OAuth2 for API, Managed Identities for Storage (No SAS tokens).
- **Enterprise Ready**: Designed for banking/FSI with audit trails and strict data separation.
