# =============================================================================
# Speech Flow - Kubernetes Deployment Script (PowerShell)
# =============================================================================
# This script deploys all Speech Flow components to AKS with proper configuration
#
# Prerequisites:
# - Azure CLI logged in (az login)
# - kubectl configured with AKS credentials
# - Helm 3 installed
# - Docker Desktop running
#
# Usage:
#   .\deploy.ps1 [-Environment prod]
#   
#   Environments: dev, staging, prod (default: prod)
# =============================================================================

param(
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment = "prod"
)

$ErrorActionPreference = "Stop"

$RESOURCE_PREFIX = "speechflow-$Environment"
$NAMESPACE = "speech-flow"
$LOCATION = "eastus"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Speech Flow Deployment - $Environment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# =============================================================================
# 1. Get values from Azure
# =============================================================================
Write-Host ""
Write-Host "Step 1: Fetching configuration from Azure..." -ForegroundColor Yellow

$RG_NAME = "rg-$RESOURCE_PREFIX-$LOCATION"

Write-Host "  - Fetching Service Bus namespace..."
$SERVICEBUS_NAMESPACE = (az servicebus namespace list -g $RG_NAME --query "[0].name" -o tsv)

Write-Host "  - Fetching Storage Account name..."
$STORAGE_ACCOUNT_NAME = (az storage account list -g $RG_NAME --query "[0].name" -o tsv)

Write-Host "  - Fetching PostgreSQL server..."
$POSTGRES_FQDN = (az postgres flexible-server list -g $RG_NAME --query "[0].fullyQualifiedDomainName" -o tsv)

Write-Host "  - Fetching Azure OpenAI endpoint..."
$AZURE_OPENAI_NAME = (az cognitiveservices account list -g $RG_NAME --query "[?kind=='OpenAI'].name | [0]" -o tsv)

Write-Host "  - Fetching Key Vault name..."
$KEY_VAULT_NAME = (az keyvault list -g $RG_NAME --query "[0].name" -o tsv)

Write-Host "  - Fetching Managed Identity Client IDs..."
$UAMI_API_CLIENT_ID = (az identity show -n "uami-$RESOURCE_PREFIX-api" -g $RG_NAME --query clientId -o tsv)
$UAMI_ROUTER_CLIENT_ID = (az identity show -n "uami-$RESOURCE_PREFIX-router" -g $RG_NAME --query clientId -o tsv)
$UAMI_WORKER_CLIENT_ID = (az identity show -n "uami-$RESOURCE_PREFIX-worker" -g $RG_NAME --query clientId -o tsv)
$UAMI_DASHBOARD_CLIENT_ID = (az identity show -n "uami-$RESOURCE_PREFIX-dashboard" -g $RG_NAME --query clientId -o tsv)
$UAMI_KEDA_CLIENT_ID = (az identity show -n "uami-$RESOURCE_PREFIX-keda" -g $RG_NAME --query clientId -o tsv)

Write-Host "  - Fetching secrets from Key Vault..."
try {
    $POSTGRES_PASSWORD = (az keyvault secret show --vault-name $KEY_VAULT_NAME -n postgres-admin-password --query value -o tsv 2>$null)
} catch { $POSTGRES_PASSWORD = "" }

try {
    $STORAGE_CONNECTION_STRING = (az keyvault secret show --vault-name $KEY_VAULT_NAME -n storage-connection-string --query value -o tsv 2>$null)
} catch { $STORAGE_CONNECTION_STRING = "" }

try {
    $SERVICEBUS_CONNECTION_STRING = (az keyvault secret show --vault-name $KEY_VAULT_NAME -n servicebus-connection-string --query value -o tsv 2>$null)
} catch { $SERVICEBUS_CONNECTION_STRING = "" }

try {
    $AZURE_OPENAI_KEY = (az keyvault secret show --vault-name $KEY_VAULT_NAME -n azure-openai-key --query value -o tsv 2>$null)
} catch { $AZURE_OPENAI_KEY = "" }

Write-Host "  ✓ Configuration fetched successfully" -ForegroundColor Green

# =============================================================================
# 2. Create temp directory for processed manifests
# =============================================================================
$TEMP_DIR = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_ }

# Function to substitute environment variables in YAML files
function Invoke-VariableSubstitution {
    param (
        [string]$InputFile,
        [string]$OutputFile
    )
    
    $content = Get-Content $InputFile -Raw
    
    # Replace all ${VAR_NAME} patterns with their values
    $vars = @{
        'SERVICEBUS_NAMESPACE' = $SERVICEBUS_NAMESPACE
        'STORAGE_ACCOUNT_NAME' = $STORAGE_ACCOUNT_NAME
        'POSTGRES_FQDN' = $POSTGRES_FQDN
        'AZURE_OPENAI_NAME' = $AZURE_OPENAI_NAME
        'KEY_VAULT_NAME' = $KEY_VAULT_NAME
        'UAMI_API_CLIENT_ID' = $UAMI_API_CLIENT_ID
        'UAMI_ROUTER_CLIENT_ID' = $UAMI_ROUTER_CLIENT_ID
        'UAMI_WORKER_CLIENT_ID' = $UAMI_WORKER_CLIENT_ID
        'UAMI_DASHBOARD_CLIENT_ID' = $UAMI_DASHBOARD_CLIENT_ID
        'UAMI_KEDA_CLIENT_ID' = $UAMI_KEDA_CLIENT_ID
        'POSTGRES_PASSWORD' = $POSTGRES_PASSWORD
        'STORAGE_CONNECTION_STRING' = $STORAGE_CONNECTION_STRING
        'SERVICEBUS_CONNECTION_STRING' = $SERVICEBUS_CONNECTION_STRING
        'AZURE_OPENAI_KEY' = $AZURE_OPENAI_KEY
        'ACR_LOGIN_SERVER' = $ACR_LOGIN_SERVER
        'IMAGE_TAG' = 'latest'
    }
    
    foreach ($key in $vars.Keys) {
        $content = $content -replace "\`$\{$key\}", $vars[$key]
    }
    
    Set-Content -Path $OutputFile -Value $content
}

# =============================================================================
# 3. Apply base Kubernetes configuration
# =============================================================================
Write-Host ""
Write-Host "Step 2: Applying base Kubernetes configuration..." -ForegroundColor Yellow

$baseOutput = Join-Path $TEMP_DIR "00-base.yaml"
Invoke-VariableSubstitution -InputFile "k8s/00-base.yaml" -OutputFile $baseOutput
kubectl apply -f $baseOutput

Write-Host "  ✓ Namespace and service accounts created" -ForegroundColor Green

# =============================================================================
# 4. Install KEDA
# =============================================================================
Write-Host ""
Write-Host "Step 3: Installing KEDA..." -ForegroundColor Yellow

helm repo add kedacore https://kedacore.github.io/charts 2>$null
helm repo update

$kedaInstalled = helm status keda -n keda 2>$null
if ($kedaInstalled) {
    Write-Host "  - KEDA already installed, upgrading..."
    $HELM_CMD = "upgrade"
} else {
    Write-Host "  - Installing KEDA..."
    kubectl create namespace keda 2>$null
    $HELM_CMD = "install"
}

helm $HELM_CMD keda kedacore/keda `
    --namespace keda `
    --set podIdentity.azureWorkload.enabled=true `
    --set podIdentity.azureWorkload.clientId=$UAMI_KEDA_CLIENT_ID `
    --set serviceAccount.create=true `
    --set serviceAccount.name=keda-operator `
    --wait

Write-Host "  ✓ KEDA installed/upgraded" -ForegroundColor Green

# =============================================================================
# 5. Configure database
# =============================================================================
Write-Host ""
Write-Host "Step 4: Configuring database..." -ForegroundColor Yellow

if ($Environment -eq "dev") {
    Write-Host "  - Deploying PostgreSQL for dev environment..."
    kubectl apply -f k8s/01-postgres.yaml
    Write-Host "  ✓ PostgreSQL deployed (dev mode)" -ForegroundColor Green
} else {
    Write-Host "  - Using Azure PostgreSQL Flexible Server"
    Write-Host "    Host: $POSTGRES_FQDN"
    Write-Host "  ✓ Database configured (production mode)" -ForegroundColor Green
}

# =============================================================================
# 6. Build and push Docker images
# =============================================================================
Write-Host ""
Write-Host "Step 5: Building Docker images..." -ForegroundColor Yellow

$ACR_NAME = (az acr list -g $RG_NAME --query "[0].name" -o tsv)
$ACR_LOGIN_SERVER = (az acr list -g $RG_NAME --query "[0].loginServer" -o tsv)

Write-Host "  - Logging into ACR..."
az acr login -n $ACR_NAME

Write-Host "  - Building backend API image..."
docker build -t "$ACR_LOGIN_SERVER/speechflow-backend:latest" -f speech-flow-backend/Dockerfile speech-flow-backend/
docker push "$ACR_LOGIN_SERVER/speechflow-backend:latest"

Write-Host "  - Building workers image..."
docker build -t "$ACR_LOGIN_SERVER/speechflow-workers:latest" -f speech-flow-workers/Dockerfile speech-flow-workers/
docker push "$ACR_LOGIN_SERVER/speechflow-workers:latest"

Write-Host "  ✓ Docker images built and pushed" -ForegroundColor Green

# =============================================================================
# 7. Deploy backend services
# =============================================================================
Write-Host ""
Write-Host "Step 6: Deploying backend services..." -ForegroundColor Yellow

$manifests = @(
    @{ Input = "k8s/02-backend-api.yaml"; Output = "02-backend-api.yaml" }
    @{ Input = "k8s/03-backend-router.yaml"; Output = "03-backend-router.yaml" }
    @{ Input = "k8s/04-backend-dashboard.yaml"; Output = "04-backend-dashboard.yaml" }
)

foreach ($manifest in $manifests) {
    $outputPath = Join-Path $TEMP_DIR $manifest.Output
    Invoke-VariableSubstitution -InputFile $manifest.Input -OutputFile $outputPath
    kubectl apply -f $outputPath
}

Write-Host "  ✓ Backend services deployed" -ForegroundColor Green

# =============================================================================
# 8. Deploy workers
# =============================================================================
Write-Host ""
Write-Host "Step 7: Deploying workers..." -ForegroundColor Yellow

$workerManifests = @(
    @{ Input = "k8s/05-worker-lid.yaml"; Output = "05-worker-lid.yaml" }
    @{ Input = "k8s/06-worker-whisper.yaml"; Output = "06-worker-whisper.yaml" }
    @{ Input = "k8s/07-worker-azure.yaml"; Output = "07-worker-azure.yaml" }
)

foreach ($manifest in $workerManifests) {
    $outputPath = Join-Path $TEMP_DIR $manifest.Output
    Invoke-VariableSubstitution -InputFile $manifest.Input -OutputFile $outputPath
    kubectl apply -f $outputPath
}

Write-Host "  ✓ Workers deployed" -ForegroundColor Green

# =============================================================================
# 9. Deploy CronJob
# =============================================================================
Write-Host ""
Write-Host "Step 8: Deploying aggregation CronJob..." -ForegroundColor Yellow

$cronOutput = Join-Path $TEMP_DIR "08-cronjob-aggregation.yaml"
Invoke-VariableSubstitution -InputFile "k8s/08-cronjob-aggregation.yaml" -OutputFile $cronOutput
kubectl apply -f $cronOutput

Write-Host "  ✓ Aggregation CronJob deployed" -ForegroundColor Green

# =============================================================================
# 10. Verify deployment
# =============================================================================
Write-Host ""
Write-Host "Step 9: Verifying deployment..." -ForegroundColor Yellow

Write-Host "  - Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=speechflow-api -n $NAMESPACE --timeout=120s 2>$null
kubectl wait --for=condition=ready pod -l app=speechflow-router -n $NAMESPACE --timeout=120s 2>$null
kubectl wait --for=condition=ready pod -l app=speechflow-dashboard -n $NAMESPACE --timeout=120s 2>$null

Write-Host ""
Write-Host "  Pod Status:" -ForegroundColor Cyan
kubectl get pods -n $NAMESPACE

Write-Host ""
Write-Host "  Service Status:" -ForegroundColor Cyan
kubectl get svc -n $NAMESPACE

Write-Host ""
Write-Host "  KEDA ScaledObjects:" -ForegroundColor Cyan
kubectl get scaledobjects -n $NAMESPACE

# =============================================================================
# 11. Get access URLs
# =============================================================================
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Yellow

$API_IP = (kubectl get svc speechflow-api -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>$null)
if (-not $API_IP) { $API_IP = "pending" }
Write-Host "  - API Gateway:  http://$($API_IP):8000"
Write-Host "  - API Docs:     http://$($API_IP):8000/docs"

$DASHBOARD_IP = (kubectl get svc speechflow-dashboard -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>$null)
if (-not $DASHBOARD_IP) { $DASHBOARD_IP = "pending" }
Write-Host "  - Dashboard:    http://$($DASHBOARD_IP):8501"

Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Yellow
Write-Host "  kubectl logs -f deployment/speechflow-api -n $NAMESPACE"
Write-Host "  kubectl logs -f deployment/speechflow-router -n $NAMESPACE"
Write-Host "  kubectl get scaledobjects -n $NAMESPACE"
Write-Host ""

# Cleanup
Remove-Item -Recurse -Force $TEMP_DIR
