#!/bin/bash
# deploy/shared/env.sh
# Reads config.yaml and exports environment variables for the selected deployment mode

set -e

# Determine script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_FILE="${PROJECT_ROOT}/config.yaml"

# Check if config.yaml exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "❌ Error: config.yaml not found at $CONFIG_FILE"
    echo "   Please copy config.sample.yaml to config.yaml and configure it."
    exit 1
fi

# Function to read YAML values (simple parser for basic key-value pairs)
read_yaml() {
    local key="$1"
    local file="$2"

    # Try python3 first (most reliable)
    if command -v python3 &> /dev/null; then
        python3 -c "import yaml, sys; data=yaml.safe_load(open('$file')); keys='$key'.split('.'); result=data; [result:=result.get(k) for k in keys]; print(result if result else '')" 2>/dev/null || echo ""
    # Fallback to grep/sed (less reliable but no dependencies)
    else
        grep "^${key}:" "$file" | head -1 | sed 's/.*: *//' | sed 's/[" ]//g' || echo ""
    fi
}

# Read deployment mode from config.yaml
DEPLOYMENT_MODE=$(read_yaml "developer_settings.deployment_mode" "$CONFIG_FILE")

# Default to online if not specified
if [[ -z "$DEPLOYMENT_MODE" ]]; then
    DEPLOYMENT_MODE="online"
    echo "⚠️  Warning: deployment_mode not found in config.yaml, defaulting to 'online'"
fi

echo "📋 Deployment Mode: $DEPLOYMENT_MODE"

# Export common environment variables
export DEPLOYMENT_MODE
export PROJECT_ROOT
export CONFIG_FILE

# Read and export TRE configuration
export TRE_ID=$(read_yaml "tre_id" "$CONFIG_FILE")
export LOCATION=$(read_yaml "location" "$CONFIG_FILE")
export RESOURCE_LOCATION="$LOCATION"

# Read developer settings
export LOGGING_LEVEL=$(read_yaml "developer_settings.logging_level" "$CONFIG_FILE")
export ENABLE_LOCAL_DEBUGGING=$(read_yaml "developer_settings.enable_local_debugging" "$CONFIG_FILE")
export ENABLE_SWAGGER=$(read_yaml "tre.enable_swagger" "$CONFIG_FILE")

# Mode-specific configuration
if [[ "$DEPLOYMENT_MODE" == "online" ]]; then
    echo "🌐 Configuring for Azure cloud deployment..."

    # Azure management configuration
    export ARM_SUBSCRIPTION_ID=$(read_yaml "management.arm_subscription_id" "$CONFIG_FILE")
    export MGMT_RESOURCE_GROUP_NAME=$(read_yaml "management.mgmt_resource_group_name" "$CONFIG_FILE")
    export MGMT_STORAGE_ACCOUNT_NAME=$(read_yaml "management.mgmt_storage_account_name" "$CONFIG_FILE")
    export ACR_NAME=$(read_yaml "management.acr_name" "$CONFIG_FILE")

    # Azure AD configuration
    export AAD_TENANT_ID=$(read_yaml "authentication.aad_tenant_id" "$CONFIG_FILE")
    export API_CLIENT_ID=$(read_yaml "authentication.api_client_id" "$CONFIG_FILE")

    # TRE configuration
    export CORE_ADDRESS_SPACE=$(read_yaml "tre.core_address_space" "$CONFIG_FILE")
    export TRE_ADDRESS_SPACE=$(read_yaml "tre.tre_address_space" "$CONFIG_FILE")

elif [[ "$DEPLOYMENT_MODE" == "offline" ]]; then
    echo "🐳 Configuring for local Docker deployment..."

    # Local emulator endpoints
    export STATE_STORE_ENDPOINT="https://localhost:8081"
    export STATE_STORE_SSL_VERIFY="false"
    export COSMOSDB_ACCOUNT_NAME="localhost"

    # Local RabbitMQ
    export SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE="localhost:5672"

    # Local Keycloak
    export AAD_TENANT_ID="local"
    export API_CLIENT_ID="tre-api-local"

    # Local network configuration (Docker networks)
    export CORE_ADDRESS_SPACE="172.20.0.0/16"
    export TRE_ADDRESS_SPACE="172.21.0.0/12"

else
    echo "❌ Error: Invalid deployment_mode '$DEPLOYMENT_MODE' (must be 'online' or 'offline')"
    exit 1
fi

# Display exported variables (for verification)
if [[ "${VERBOSE:-0}" == "1" ]]; then
    echo ""
    echo "Exported environment variables:"
    echo "  DEPLOYMENT_MODE=$DEPLOYMENT_MODE"
    echo "  TRE_ID=$TRE_ID"
    echo "  LOCATION=$LOCATION"
    if [[ "$DEPLOYMENT_MODE" == "online" ]]; then
        echo "  ARM_SUBSCRIPTION_ID=$ARM_SUBSCRIPTION_ID"
        echo "  ACR_NAME=$ACR_NAME"
    else
        echo "  STATE_STORE_ENDPOINT=$STATE_STORE_ENDPOINT"
        echo "  SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE=$SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE"
    fi
fi

echo "✅ Environment configured for $DEPLOYMENT_MODE mode"