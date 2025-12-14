# Speech Flow - Terraform Infrastructure
# This file provisions all Azure resources needed for the Speech Flow platform

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.45"
    }
  }
  
  # Uncomment for remote state
  # backend "azurerm" {
  #   resource_group_name  = "rg-terraform-state"
  #   storage_account_name = "sttfstate"
  #   container_name       = "tfstate"
  #   key                  = "speechflow.tfstate"
  # }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false
    }
  }
}

provider "azuread" {}

# =============================================================================
# VARIABLES
# =============================================================================

variable "project" {
  description = "Project name"
  type        = string
  default     = "speechflow"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "postgres_admin_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}

variable "aks_node_count" {
  description = "Number of nodes in default pool"
  type        = number
  default     = 2
}

variable "enable_gpu_pool" {
  description = "Enable GPU node pool for Whisper"
  type        = bool
  default     = true
}

locals {
  resource_prefix = "${var.project}-${var.environment}"
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# =============================================================================
# DATA SOURCES
# =============================================================================

data "azurerm_client_config" "current" {}

# =============================================================================
# RESOURCE GROUP
# =============================================================================

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.resource_prefix}-${var.location}"
  location = var.location
  tags     = local.common_tags
}

# =============================================================================
# MANAGED IDENTITIES
# =============================================================================

resource "azurerm_user_assigned_identity" "api" {
  name                = "uami-${local.resource_prefix}-api"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.common_tags
}

resource "azurerm_user_assigned_identity" "router" {
  name                = "uami-${local.resource_prefix}-router"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.common_tags
}

resource "azurerm_user_assigned_identity" "worker" {
  name                = "uami-${local.resource_prefix}-worker"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.common_tags
}

resource "azurerm_user_assigned_identity" "keda" {
  name                = "uami-${local.resource_prefix}-keda"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.common_tags
}

resource "azurerm_user_assigned_identity" "dashboard" {
  name                = "uami-${local.resource_prefix}-dashboard"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = local.common_tags
}

# =============================================================================
# AZURE SERVICE BUS
# =============================================================================

resource "azurerm_servicebus_namespace" "main" {
  name                = "sb-${local.resource_prefix}-${var.location}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Standard"
  tags                = local.common_tags
}

resource "azurerm_servicebus_queue" "job_events" {
  name         = "job-events"
  namespace_id = azurerm_servicebus_namespace.main.id
  
  enable_partitioning                  = false
  dead_lettering_on_message_expiration = true
  max_delivery_count                   = 10
  default_message_ttl                  = "P14D"
}

resource "azurerm_servicebus_queue" "lid_jobs" {
  name         = "lid-jobs"
  namespace_id = azurerm_servicebus_namespace.main.id
  
  enable_partitioning                  = false
  dead_lettering_on_message_expiration = true
  max_delivery_count                   = 10
  default_message_ttl                  = "P14D"
}

resource "azurerm_servicebus_queue" "whisper_jobs" {
  name         = "whisper-jobs"
  namespace_id = azurerm_servicebus_namespace.main.id
  
  enable_partitioning                  = false
  dead_lettering_on_message_expiration = true
  max_delivery_count                   = 10
  default_message_ttl                  = "P14D"
}

resource "azurerm_servicebus_queue" "azure_ai_jobs" {
  name         = "azure-ai-jobs"
  namespace_id = azurerm_servicebus_namespace.main.id
  
  enable_partitioning                  = false
  dead_lettering_on_message_expiration = true
  max_delivery_count                   = 10
  default_message_ttl                  = "P14D"
}

# =============================================================================
# AZURE STORAGE
# =============================================================================

resource "azurerm_storage_account" "main" {
  name                     = "st${var.project}${var.environment}${substr(var.location, 0, 4)}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  
  blob_properties {
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "PUT", "POST"]
      allowed_origins    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }
  }
  
  tags = local.common_tags
}

resource "azurerm_storage_container" "audio_files" {
  name                  = "audio-files"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "results" {
  name                  = "results"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# =============================================================================
# AZURE POSTGRESQL FLEXIBLE SERVER
# =============================================================================

resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "psql-${local.resource_prefix}-${var.location}"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "15"
  administrator_login    = "${var.project}admin"
  administrator_password = var.postgres_admin_password
  
  storage_mb = 32768
  sku_name   = "B_Standard_B2s"
  
  zone = "1"
  
  tags = local.common_tags
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = var.project
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# =============================================================================
# AZURE OPENAI
# =============================================================================

resource "azurerm_cognitive_account" "openai" {
  name                  = "aoai-${local.resource_prefix}-${var.location}"
  resource_group_name   = azurerm_resource_group.main.name
  location              = var.location
  kind                  = "OpenAI"
  sku_name              = "S0"
  custom_subdomain_name = "aoai-${local.resource_prefix}-${var.location}"
  
  tags = local.common_tags
}

resource "azurerm_cognitive_deployment" "gpt4" {
  name                 = "gpt-4"
  cognitive_account_id = azurerm_cognitive_account.openai.id
  
  model {
    format  = "OpenAI"
    name    = "gpt-4"
    version = "0613"
  }
  
  scale {
    type     = "Standard"
    capacity = 10
  }
}

# =============================================================================
# AZURE CONTAINER REGISTRY
# =============================================================================

resource "azurerm_container_registry" "main" {
  name                = "acr${var.project}${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Standard"
  admin_enabled       = false
  
  tags = local.common_tags
}

# =============================================================================
# AZURE KEY VAULT
# =============================================================================

resource "azurerm_key_vault" "main" {
  name                       = "kv-${local.resource_prefix}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  enable_rbac_authorization  = true
  purge_protection_enabled   = true
  soft_delete_retention_days = 7
  
  tags = local.common_tags
}

# Store secrets in Key Vault
resource "azurerm_key_vault_secret" "database_url" {
  name         = "database-url"
  value        = "postgresql://${azurerm_postgresql_flexible_server.main.administrator_login}:${var.postgres_admin_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${var.project}?sslmode=require"
  key_vault_id = azurerm_key_vault.main.id
  
  depends_on = [azurerm_role_assignment.terraform_kv_admin]
}

resource "azurerm_key_vault_secret" "servicebus_connection" {
  name         = "servicebus-connection-string"
  value        = azurerm_servicebus_namespace.main.default_primary_connection_string
  key_vault_id = azurerm_key_vault.main.id
  
  depends_on = [azurerm_role_assignment.terraform_kv_admin]
}

resource "azurerm_key_vault_secret" "storage_connection" {
  name         = "storage-connection-string"
  value        = azurerm_storage_account.main.primary_connection_string
  key_vault_id = azurerm_key_vault.main.id
  
  depends_on = [azurerm_role_assignment.terraform_kv_admin]
}

resource "azurerm_key_vault_secret" "openai_endpoint" {
  name         = "azure-openai-endpoint"
  value        = azurerm_cognitive_account.openai.endpoint
  key_vault_id = azurerm_key_vault.main.id
  
  depends_on = [azurerm_role_assignment.terraform_kv_admin]
}

resource "azurerm_key_vault_secret" "openai_key" {
  name         = "azure-openai-key"
  value        = azurerm_cognitive_account.openai.primary_access_key
  key_vault_id = azurerm_key_vault.main.id
  
  depends_on = [azurerm_role_assignment.terraform_kv_admin]
}

# Allow Terraform to manage secrets
resource "azurerm_role_assignment" "terraform_kv_admin" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# =============================================================================
# AZURE KUBERNETES SERVICE
# =============================================================================

resource "azurerm_kubernetes_cluster" "main" {
  name                = "aks-${local.resource_prefix}-${var.location}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "aks-${local.resource_prefix}"
  
  oidc_issuer_enabled       = true
  workload_identity_enabled = true
  
  default_node_pool {
    name                = "system"
    node_count          = var.aks_node_count
    vm_size             = "Standard_D4s_v3"
    enable_auto_scaling = true
    min_count           = 2
    max_count           = 5
    
    node_labels = {
      "pool" = "system"
    }
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  network_profile {
    network_plugin = "azure"
    network_policy = "azure"
  }
  
  tags = local.common_tags
}

# CPU Node Pool (for backend services and LID worker)
resource "azurerm_kubernetes_cluster_node_pool" "cpu" {
  name                  = "cpupool"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = "Standard_D4s_v3"
  node_count            = 2
  enable_auto_scaling   = true
  min_count             = 1
  max_count             = 10
  
  node_labels = {
    "pool" = "cpu"
  }
  
  tags = local.common_tags
}

# GPU Node Pool (for Whisper worker)
resource "azurerm_kubernetes_cluster_node_pool" "gpu" {
  count                 = var.enable_gpu_pool ? 1 : 0
  name                  = "gpupool"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = "Standard_NC6s_v3"
  node_count            = 0
  enable_auto_scaling   = true
  min_count             = 0
  max_count             = 5
  
  node_labels = {
    "pool" = "gpu"
  }
  
  node_taints = [
    "sku=gpu:NoSchedule"
  ]
  
  tags = local.common_tags
}

# Attach ACR to AKS
resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
}

# =============================================================================
# RBAC ROLE ASSIGNMENTS
# =============================================================================

# API Identity - Storage Blob Data Contributor
resource "azurerm_role_assignment" "api_storage" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}

# API Identity - Service Bus Data Sender
resource "azurerm_role_assignment" "api_servicebus" {
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}

# API Identity - Key Vault Secrets User
resource "azurerm_role_assignment" "api_keyvault" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.api.principal_id
}

# Router Identity - Service Bus Data Sender
resource "azurerm_role_assignment" "router_servicebus_sender" {
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = azurerm_user_assigned_identity.router.principal_id
}

# Router Identity - Service Bus Data Receiver
resource "azurerm_role_assignment" "router_servicebus_receiver" {
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Receiver"
  principal_id         = azurerm_user_assigned_identity.router.principal_id
}

# Router Identity - Key Vault Secrets User
resource "azurerm_role_assignment" "router_keyvault" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.router.principal_id
}

# Worker Identity - Storage Blob Data Contributor
resource "azurerm_role_assignment" "worker_storage" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.worker.principal_id
}

# Worker Identity - Service Bus Data Sender
resource "azurerm_role_assignment" "worker_servicebus_sender" {
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Sender"
  principal_id         = azurerm_user_assigned_identity.worker.principal_id
}

# Worker Identity - Service Bus Data Receiver
resource "azurerm_role_assignment" "worker_servicebus_receiver" {
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Receiver"
  principal_id         = azurerm_user_assigned_identity.worker.principal_id
}

# Worker Identity - Cognitive Services OpenAI User
resource "azurerm_role_assignment" "worker_openai" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_user_assigned_identity.worker.principal_id
}

# Worker Identity - Key Vault Secrets User
resource "azurerm_role_assignment" "worker_keyvault" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.worker.principal_id
}

# KEDA Identity - Service Bus Data Receiver (for queue monitoring)
resource "azurerm_role_assignment" "keda_servicebus" {
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Receiver"
  principal_id         = azurerm_user_assigned_identity.keda.principal_id
}

# Dashboard Identity - Service Bus Data Receiver
resource "azurerm_role_assignment" "dashboard_servicebus" {
  scope                = azurerm_servicebus_namespace.main.id
  role_definition_name = "Azure Service Bus Data Receiver"
  principal_id         = azurerm_user_assigned_identity.dashboard.principal_id
}

# Dashboard Identity - Key Vault Secrets User
resource "azurerm_role_assignment" "dashboard_keyvault" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.dashboard.principal_id
}

# =============================================================================
# FEDERATED CREDENTIALS FOR WORKLOAD IDENTITY
# =============================================================================

resource "azurerm_federated_identity_credential" "api" {
  name                = "fc-${local.resource_prefix}-api"
  resource_group_name = azurerm_resource_group.main.name
  parent_id           = azurerm_user_assigned_identity.api.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.main.oidc_issuer_url
  subject             = "system:serviceaccount:speech-flow:sa-speechflow-api"
}

resource "azurerm_federated_identity_credential" "router" {
  name                = "fc-${local.resource_prefix}-router"
  resource_group_name = azurerm_resource_group.main.name
  parent_id           = azurerm_user_assigned_identity.router.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.main.oidc_issuer_url
  subject             = "system:serviceaccount:speech-flow:sa-speechflow-router"
}

resource "azurerm_federated_identity_credential" "worker" {
  name                = "fc-${local.resource_prefix}-worker"
  resource_group_name = azurerm_resource_group.main.name
  parent_id           = azurerm_user_assigned_identity.worker.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.main.oidc_issuer_url
  subject             = "system:serviceaccount:speech-flow:sa-speechflow-worker"
}

resource "azurerm_federated_identity_credential" "dashboard" {
  name                = "fc-${local.resource_prefix}-dashboard"
  resource_group_name = azurerm_resource_group.main.name
  parent_id           = azurerm_user_assigned_identity.dashboard.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.main.oidc_issuer_url
  subject             = "system:serviceaccount:speech-flow:sa-speechflow-dashboard"
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.main.name
}

output "aks_cluster_fqdn" {
  value = azurerm_kubernetes_cluster.main.fqdn
}

output "acr_login_server" {
  value = azurerm_container_registry.main.login_server
}

output "servicebus_namespace" {
  value = azurerm_servicebus_namespace.main.name
}

output "storage_account_name" {
  value = azurerm_storage_account.main.name
}

output "postgresql_fqdn" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}

output "openai_endpoint" {
  value = azurerm_cognitive_account.openai.endpoint
}

output "key_vault_name" {
  value = azurerm_key_vault.main.name
}

output "identity_client_ids" {
  value = {
    api       = azurerm_user_assigned_identity.api.client_id
    router    = azurerm_user_assigned_identity.router.client_id
    worker    = azurerm_user_assigned_identity.worker.client_id
    keda      = azurerm_user_assigned_identity.keda.client_id
    dashboard = azurerm_user_assigned_identity.dashboard.client_id
  }
}

output "aks_oidc_issuer_url" {
  value = azurerm_kubernetes_cluster.main.oidc_issuer_url
}

output "get_credentials_command" {
  value = "az aks get-credentials --name ${azurerm_kubernetes_cluster.main.name} --resource-group ${azurerm_resource_group.main.name}"
}
