# Hybrid Development Guide

This guide explains how to run the Speech Flow application locally while connecting to real Azure resources (Hybrid Mode). This is useful for testing integration with Azure services (Service Bus, Blob Storage, SQL) without deploying the application code to the cloud.

## Prerequisites

1.  **Azure Resources**: You must have the following resources created in Azure:
    *   **Azure Service Bus Namespace** (Standard or Premium tier)
    *   **Azure Storage Account**
    *   **Azure SQL Database** (or a local Postgres instance accessible from Docker)
    *   **Azure OpenAI Service** (optional, for AI worker)
    *   **Service Principal**: An Azure Service Principal with the following roles:
        *   `Azure Service Bus Data Owner` (on the Service Bus Namespace)
        *   `Storage Blob Data Contributor` (on the Storage Account)

2.  **Credentials**: You need the Client ID, Client Secret, and Tenant ID for the Service Principal.

## Configuration

1.  Create a `.env` file in the root directory (or copy `.env.example` if available).
2.  Add the following variables to your `.env` file:

```env
# Environment Settings
ENVIRONMENT=LOCAL
USE_CLOUD_RESOURCES=true

# Service Principal Authentication
AZURE_CLIENT_ID="<your-client-id>"
AZURE_CLIENT_SECRET="<your-client-secret>"
AZURE_TENANT_ID="<your-tenant-id>"

# Azure Service Bus
SERVICEBUS_NAMESPACE="<your-namespace-name>"
# Example: if your FQDN is mybus.servicebus.windows.net, use "mybus"
ROUTER_QUEUE_NAME=job-events
LID_QUEUE_NAME=lid-jobs
WHISPER_QUEUE_NAME=whisper-jobs
AZURE_AI_QUEUE_NAME=azure-ai-jobs

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME="<your-storage-account-name>"
BLOB_CONTAINER_NAME=raw-audio
RESULTS_CONTAINER_NAME=results

# Database
# Note: If using Azure SQL, ensure your IP is allowed in the firewall settings.
DATABASE_URL="postgresql://<user>:<password>@<host>:5432/<database>"

# Azure OpenAI (Optional)
AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com/"
AZURE_OPENAI_KEY="<your-key>"
AZURE_OPENAI_DEPLOYMENT="gpt-4"
```

## Running in Hybrid Mode

To start the application in hybrid mode, use the `docker-compose.hybrid.yml` file:

```bash
docker-compose -f docker-compose.hybrid.yml up --build
```

## Architecture

In this mode:
*   **Compute**: Runs locally in Docker containers (API, Router, Workers).
*   **Messaging**: Uses Azure Service Bus via `DefaultAzureCredential` (Service Principal).
*   **Storage**: Uses Azure Blob Storage via `DefaultAzureCredential` (Service Principal).
*   **Database**: Connects to the configured database URL.

## Troubleshooting

*   **Authentication Errors**: Ensure your Service Principal has the correct roles (`Azure Service Bus Data Owner`, `Storage Blob Data Contributor`).
*   **Connection Issues**: Ensure your local machine's IP address is whitelisted in the Azure resources' firewalls.

