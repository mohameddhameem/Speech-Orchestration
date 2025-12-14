#!/bin/bash
# =============================================================================
# Speech Flow - Kubernetes Deployment Script
# =============================================================================
# This script deploys all Speech Flow components to AKS with proper configuration
#
# Prerequisites:
# - Azure CLI logged in (az login)
# - kubectl configured with AKS credentials
# - Helm 3 installed
# - jq installed
#
# Usage:
#   ./deploy.sh [environment]
#   
#   Environments: dev, staging, prod (default: prod)
# =============================================================================

set -e

ENVIRONMENT="${1:-prod}"
RESOURCE_PREFIX="speechflow-${ENVIRONMENT}"
NAMESPACE="speech-flow"

echo "=========================================="
echo "Speech Flow Deployment - ${ENVIRONMENT}"
echo "=========================================="

# =============================================================================
# 1. Get values from Terraform or Azure
# =============================================================================
echo ""
echo "Step 1: Fetching configuration from Azure..."

# Get resource group name
RG_NAME="rg-${RESOURCE_PREFIX}-eastus"

# Get values from Azure resources
echo "  - Fetching Service Bus namespace..."
SERVICEBUS_NAMESPACE=$(az servicebus namespace list -g $RG_NAME --query "[0].name" -o tsv)

echo "  - Fetching Storage Account name..."
STORAGE_ACCOUNT_NAME=$(az storage account list -g $RG_NAME --query "[0].name" -o tsv)

echo "  - Fetching PostgreSQL server..."
POSTGRES_FQDN=$(az postgres flexible-server list -g $RG_NAME --query "[0].fullyQualifiedDomainName" -o tsv)

echo "  - Fetching Azure OpenAI endpoint..."
AZURE_OPENAI_NAME=$(az cognitiveservices account list -g $RG_NAME --query "[?kind=='OpenAI'].name | [0]" -o tsv)

echo "  - Fetching Key Vault name..."
KEY_VAULT_NAME=$(az keyvault list -g $RG_NAME --query "[0].name" -o tsv)

echo "  - Fetching Managed Identity Client IDs..."
UAMI_API_CLIENT_ID=$(az identity show -n "uami-${RESOURCE_PREFIX}-api" -g $RG_NAME --query clientId -o tsv)
UAMI_ROUTER_CLIENT_ID=$(az identity show -n "uami-${RESOURCE_PREFIX}-router" -g $RG_NAME --query clientId -o tsv)
UAMI_WORKER_CLIENT_ID=$(az identity show -n "uami-${RESOURCE_PREFIX}-worker" -g $RG_NAME --query clientId -o tsv)
UAMI_DASHBOARD_CLIENT_ID=$(az identity show -n "uami-${RESOURCE_PREFIX}-dashboard" -g $RG_NAME --query clientId -o tsv)
UAMI_KEDA_CLIENT_ID=$(az identity show -n "uami-${RESOURCE_PREFIX}-keda" -g $RG_NAME --query clientId -o tsv)

echo "  - Fetching secrets from Key Vault..."
POSTGRES_PASSWORD=$(az keyvault secret show --vault-name $KEY_VAULT_NAME -n postgres-admin-password --query value -o tsv 2>/dev/null || echo "")
STORAGE_CONNECTION_STRING=$(az keyvault secret show --vault-name $KEY_VAULT_NAME -n storage-connection-string --query value -o tsv 2>/dev/null || echo "")
SERVICEBUS_CONNECTION_STRING=$(az keyvault secret show --vault-name $KEY_VAULT_NAME -n servicebus-connection-string --query value -o tsv 2>/dev/null || echo "")
AZURE_OPENAI_KEY=$(az keyvault secret show --vault-name $KEY_VAULT_NAME -n azure-openai-key --query value -o tsv 2>/dev/null || echo "")

echo "  ✓ Configuration fetched successfully"

# =============================================================================
# 2. Create namespace and apply base configuration
# =============================================================================
echo ""
echo "Step 2: Applying base Kubernetes configuration..."

# Create temp directory for processed manifests
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Process 00-base.yaml with variable substitution
envsubst < k8s/00-base.yaml > $TEMP_DIR/00-base.yaml
kubectl apply -f $TEMP_DIR/00-base.yaml

echo "  ✓ Namespace and service accounts created"

# =============================================================================
# 3. Install KEDA with Workload Identity
# =============================================================================
echo ""
echo "Step 3: Installing KEDA..."

# Add KEDA Helm repo
helm repo add kedacore https://kedacore.github.io/charts 2>/dev/null || true
helm repo update

# Check if KEDA is already installed
if helm status keda -n keda >/dev/null 2>&1; then
    echo "  - KEDA already installed, upgrading..."
    HELM_CMD="upgrade"
else
    echo "  - Installing KEDA..."
    kubectl create namespace keda 2>/dev/null || true
    HELM_CMD="install"
fi

helm $HELM_CMD keda kedacore/keda \
    --namespace keda \
    --set podIdentity.azureWorkload.enabled=true \
    --set podIdentity.azureWorkload.clientId=$UAMI_KEDA_CLIENT_ID \
    --set serviceAccount.create=true \
    --set serviceAccount.name=keda-operator \
    --wait

echo "  ✓ KEDA installed/upgraded"

# =============================================================================
# 4. Deploy PostgreSQL (for dev) or configure connection (for prod)
# =============================================================================
echo ""
echo "Step 4: Configuring database..."

if [ "$ENVIRONMENT" == "dev" ]; then
    echo "  - Deploying PostgreSQL for dev environment..."
    kubectl apply -f k8s/01-postgres.yaml
    echo "  ✓ PostgreSQL deployed (dev mode)"
else
    echo "  - Using Azure PostgreSQL Flexible Server"
    echo "    Host: $POSTGRES_FQDN"
    echo "  ✓ Database configured (production mode)"
fi

# =============================================================================
# 5. Build and push Docker images
# =============================================================================
echo ""
echo "Step 5: Building Docker images..."

ACR_NAME=$(az acr list -g $RG_NAME --query "[0].name" -o tsv)
ACR_LOGIN_SERVER=$(az acr list -g $RG_NAME --query "[0].loginServer" -o tsv)

echo "  - Logging into ACR..."
az acr login -n $ACR_NAME

echo "  - Building backend API image..."
docker build -t $ACR_LOGIN_SERVER/speechflow-backend:latest -f speech-flow-backend/Dockerfile speech-flow-backend/
docker push $ACR_LOGIN_SERVER/speechflow-backend:latest

echo "  - Building workers image..."
docker build -t $ACR_LOGIN_SERVER/speechflow-workers:latest -f speech-flow-workers/Dockerfile speech-flow-workers/
docker push $ACR_LOGIN_SERVER/speechflow-workers:latest

echo "  ✓ Docker images built and pushed"

# =============================================================================
# 6. Deploy backend services
# =============================================================================
echo ""
echo "Step 6: Deploying backend services..."

# Set image tag
export IMAGE_TAG="latest"
export ACR_LOGIN_SERVER

# Apply API deployment
envsubst < k8s/02-backend-api.yaml > $TEMP_DIR/02-backend-api.yaml
kubectl apply -f $TEMP_DIR/02-backend-api.yaml

# Apply Router deployment
envsubst < k8s/03-backend-router.yaml > $TEMP_DIR/03-backend-router.yaml
kubectl apply -f $TEMP_DIR/03-backend-router.yaml

# Apply Dashboard deployment
envsubst < k8s/04-backend-dashboard.yaml > $TEMP_DIR/04-backend-dashboard.yaml
kubectl apply -f $TEMP_DIR/04-backend-dashboard.yaml

echo "  ✓ Backend services deployed"

# =============================================================================
# 7. Deploy workers with KEDA autoscaling
# =============================================================================
echo ""
echo "Step 7: Deploying workers..."

# Apply LID Worker
envsubst < k8s/05-worker-lid.yaml > $TEMP_DIR/05-worker-lid.yaml
kubectl apply -f $TEMP_DIR/05-worker-lid.yaml

# Apply Whisper Worker
envsubst < k8s/06-worker-whisper.yaml > $TEMP_DIR/06-worker-whisper.yaml
kubectl apply -f $TEMP_DIR/06-worker-whisper.yaml

# Apply Azure AI Worker
envsubst < k8s/07-worker-azure.yaml > $TEMP_DIR/07-worker-azure.yaml
kubectl apply -f $TEMP_DIR/07-worker-azure.yaml

echo "  ✓ Workers deployed"

# =============================================================================
# 8. Deploy CronJob for daily aggregation
# =============================================================================
echo ""
echo "Step 8: Deploying aggregation CronJob..."

envsubst < k8s/08-cronjob-aggregation.yaml > $TEMP_DIR/08-cronjob-aggregation.yaml
kubectl apply -f $TEMP_DIR/08-cronjob-aggregation.yaml

echo "  ✓ Aggregation CronJob deployed"

# =============================================================================
# 9. Verify deployment
# =============================================================================
echo ""
echo "Step 9: Verifying deployment..."

echo "  - Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=speechflow-api -n $NAMESPACE --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=speechflow-router -n $NAMESPACE --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=speechflow-dashboard -n $NAMESPACE --timeout=120s || true

echo ""
echo "  Pod Status:"
kubectl get pods -n $NAMESPACE

echo ""
echo "  Service Status:"
kubectl get svc -n $NAMESPACE

echo ""
echo "  KEDA ScaledObjects:"
kubectl get scaledobjects -n $NAMESPACE

# =============================================================================
# 10. Get access URLs
# =============================================================================
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Access URLs:"

# Get API external IP
API_IP=$(kubectl get svc speechflow-api -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
echo "  - API Gateway:  http://${API_IP}:8000"
echo "  - API Docs:     http://${API_IP}:8000/docs"

# Get Dashboard external IP
DASHBOARD_IP=$(kubectl get svc speechflow-dashboard -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
echo "  - Dashboard:    http://${DASHBOARD_IP}:8501"

echo ""
echo "Useful Commands:"
echo "  kubectl logs -f deployment/speechflow-api -n $NAMESPACE"
echo "  kubectl logs -f deployment/speechflow-router -n $NAMESPACE"
echo "  kubectl get scaledobjects -n $NAMESPACE"
echo ""
