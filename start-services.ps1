# Start Speech-Flow services using Podman
# This script starts services in the correct order with health checks

Write-Host "Starting Speech-Flow services..." -ForegroundColor Green

# Create network if it doesn't exist
Write-Host "`nCreating network..." -ForegroundColor Cyan
podman network create speech-flow 2>$null

# Create volumes
Write-Host "Creating volumes..." -ForegroundColor Cyan
podman volume create postgres_data 2>$null
podman volume create model_cache 2>$null

# Start PostgreSQL
Write-Host "`nStarting PostgreSQL..." -ForegroundColor Cyan
podman run -d `
  --name speechflow-postgres `
  --network speech-flow `
  -e POSTGRES_USER=user `
  -e POSTGRES_PASSWORD=password `
  -e POSTGRES_DB=speechflow `
  -p 5432:5432 `
  -v postgres_data:/var/lib/postgresql/data `
  -v ${PWD}/speech-flow-infra/database/schema.sql:/docker-entrypoint-initdb.d/schema.sql:ro `
  --cap-drop=ALL --cap-add=SETUID --cap-add=SETGID --cap-add=CHOWN --cap-add=DAC_OVERRIDE `
  --security-opt=no-new-privileges:true `
  postgres:14-alpine

# Wait for PostgreSQL to be healthy
Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Start Azurite
Write-Host "`nStarting Azurite..." -ForegroundColor Cyan
podman run -d `
  --name speechflow-azurite `
  --network speech-flow `
  -p 10000:10000 -p 10001:10001 -p 10002:10002 `
  --security-opt=no-new-privileges:true `
  mcr.microsoft.com/azure-storage/azurite:3.27.0 `
  azurite-blob --blobHost 0.0.0.0 --blobPort 10000 --silent --skipApiVersionCheck

# Wait for Azurite to be ready
Write-Host "Waiting for Azurite to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start RabbitMQ (for local message broker)
Write-Host "`nStarting RabbitMQ..." -ForegroundColor Cyan
podman run -d `
  --name rabbitmq `
  --network speech-flow `
  -p 5672:5672 -p 15672:15672 `
  -e RABBITMQ_DEFAULT_USER=guest `
  -e RABBITMQ_DEFAULT_PASS=guest `
  rabbitmq:3-management

Write-Host "Waiting for RabbitMQ to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Start API
Write-Host "`nStarting API service..." -ForegroundColor Cyan
podman run -d `
  --name speechflow-api `
  --network speech-flow `
  -e ENVIRONMENT=LOCAL `
  -e DATABASE_URL=postgresql://user:password@speechflow-postgres:5432/speechflow `
  -e AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://speechflow-azurite:10000/devstoreaccount1;" `
  -e SERVICEBUS_CONNECTION_STRING=$env:SERVICEBUS_CONNECTION_STRING `
  -p 8000:8000 `
  -v ${PWD}/speech-flow-backend:/app `
  --cap-drop=ALL --cap-add=NET_BIND_SERVICE `
  --security-opt=no-new-privileges:true `
  localhost/speechflow-backend:latest `
  uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Start Router
Write-Host "`nStarting Router service..." -ForegroundColor Cyan
podman run -d `
  --name speechflow-router `
  --network speech-flow `
  -e ENVIRONMENT=LOCAL `
  -e DATABASE_URL=postgresql://user:password@speechflow-postgres:5432/speechflow `
  -e RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/" `
  -e AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://speechflow-azurite:10000/devstoreaccount1;" `
  --cap-drop=ALL `
  --security-opt=no-new-privileges:true `
  localhost/speechflow-backend:latest `
  python router/main.py

# Start Dashboard
Write-Host "`nStarting Dashboard service..." -ForegroundColor Cyan
podman run -d `
  --name speechflow-dashboard `
  --network speech-flow `
  -e ENVIRONMENT=LOCAL `
  -e DATABASE_URL=postgresql://user:password@speechflow-postgres:5432/speechflow `
  -e SERVICEBUS_CONNECTION_STRING=$env:SERVICEBUS_CONNECTION_STRING `
  -e STREAMLIT_CONFIG_DIR=/tmp/.streamlit `
  -e HOME=/tmp `
  -e STREAMLIT_BROWSER_GATHERUSAGESTATS=false `
  -p 8501:8501 `
  --cap-drop=ALL --cap-add=NET_BIND_SERVICE `
  --security-opt=no-new-privileges:true `
  localhost/speechflow-backend:latest `
  streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0

# =====================
# Prepare Azure blobs for workers
# =====================
Write-Host "`nEnsuring Azurite containers exist..." -ForegroundColor Cyan
podman run --rm `
  --network speech-flow `
  -e AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://speechflow-azurite:10000/devstoreaccount1;" `
  -v ${PWD}/speech-flow-infra/storage:/scripts:ro `
  localhost/speechflow-backend:latest `
  python /scripts/init_containers.py

# =====================
# Start Workers (must finish before UI comes online)
# =====================
Write-Host "`nStarting Workers (this builds the worker image, which installs large ML packages like torch)..." -ForegroundColor Cyan

# Build workers image (uses speech-flow-workers/Dockerfile)
podman build -t localhost/speechflow-workers:latest -f ${PWD}/speech-flow-workers/Dockerfile ${PWD} 2>$null

Write-Host "Starting worker containers: lid, whisper, azure" -ForegroundColor Cyan

# LID Worker
podman run -d `
  --name speechflow-worker-lid `
  --network speech-flow `
  -e ENVIRONMENT=LOCAL `
  -e DATABASE_URL=postgresql://user:password@speechflow-postgres:5432/speechflow `
  -e RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/" `
  -e AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://speechflow-azurite:10000/devstoreaccount1;" `
  --cap-drop=ALL `
  --security-opt=no-new-privileges:true `
  -v ${PWD}/speech-flow-workers:/app `
  localhost/speechflow-workers:latest `
  python lid/worker.py

# Whisper Worker
podman run -d `
  --name speechflow-worker-whisper `
  --network speech-flow `
  -e ENVIRONMENT=LOCAL `
  -e DATABASE_URL=postgresql://user:password@speechflow-postgres:5432/speechflow `
  -e RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/" `
  -e AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://speechflow-azurite:10000/devstoreaccount1;" `
  --cap-drop=ALL `
  --security-opt=no-new-privileges:true `
  -v ${PWD}/speech-flow-workers:/app `
  localhost/speechflow-workers:latest `
  python whisper/worker.py

# Azure AI Worker
podman run -d `
  --name speechflow-worker-azure `
  --network speech-flow `
  -e ENVIRONMENT=LOCAL `
  -e DATABASE_URL=postgresql://user:password@speechflow-postgres:5432/speechflow `
  -e RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/" `
  -e AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://speechflow-azurite:10000/devstoreaccount1;" `
  --cap-drop=ALL `
  --security-opt=no-new-privileges:true `
  -v ${PWD}/speech-flow-workers:/app `
  localhost/speechflow-workers:latest `
  python azure_ai/worker.py

Write-Host "`nWorkers started: lid, whisper, azure" -ForegroundColor Green

# =====================
# Optional: Start UI
# =====================
Write-Host "`nBuilding UI image..." -ForegroundColor Cyan
podman build -t localhost/speechflow-ui:latest -f ${PWD}/speech-flow-ui/Dockerfile ${PWD} 2>$null

Write-Host "Starting UI service..." -ForegroundColor Cyan
podman run -d `
  --name speechflow-ui `
  --network speech-flow `
  -e API_BASE_URL="http://speechflow-api:8000" `
  -p 8502:8502 `
  --cap-drop=ALL --cap-add=NET_BIND_SERVICE `
  --security-opt=no-new-privileges:true `
  localhost/speechflow-ui:latest `
  streamlit run app.py --server.port=8502 --server.address=0.0.0.0

Write-Host "`n✅ All services started!" -ForegroundColor Green
Write-Host "`nService URLs (UI included):" -ForegroundColor Cyan
Write-Host "  API:         http://localhost:8000" -ForegroundColor White
Write-Host "  Dashboard:   http://localhost:8501" -ForegroundColor White
Write-Host "  UI:          http://localhost:8502" -ForegroundColor White
Write-Host "  Postgres:    localhost:5432" -ForegroundColor White
Write-Host "  Azurite:     localhost:10000" -ForegroundColor White
Write-Host "  RabbitMQ:    localhost:15672 (user: guest, pass: guest)" -ForegroundColor White

Write-Host "`nCheck status with: podman ps" -ForegroundColor Yellow
Write-Host "View logs with: podman logs <container-name>" -ForegroundColor Yellow
Write-Host "Stop all with: podman stop speechflow-api speechflow-router speechflow-dashboard speechflow-postgres speechflow-azurite rabbitmq speechflow-ui" -ForegroundColor Yellow

