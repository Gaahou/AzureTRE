#!/bin/bash
# deploy/shared/healthcheck.sh
# Mode-agnostic health check for Azure TRE API

set -e

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source environment configuration
if [[ -f "$SCRIPT_DIR/env.sh" ]]; then
    source "$SCRIPT_DIR/env.sh" > /dev/null 2>&1 || true
fi

# Detect deployment mode
DEPLOYMENT_MODE="${DEPLOYMENT_MODE:-online}"

# Determine API endpoint based on mode
if [[ "$DEPLOYMENT_MODE" == "offline" ]]; then
    API_ENDPOINT="${TRE_URL:-http://localhost:8000}"
else
    # For online mode, try to get from environment or use default
    API_ENDPOINT="${TRE_URL:-https://api-${TRE_ID}.azurewebsites.net}"
fi

echo "🔍 TRE Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Mode:     $DEPLOYMENT_MODE"
echo "Endpoint: $API_ENDPOINT"
echo ""

# Function to check HTTP endpoint
check_endpoint() {
    local url="$1"
    local name="$2"
    local timeout="${3:-5}"

    echo -n "Checking $name... "

    if curl -sf --max-time "$timeout" "$url" > /dev/null 2>&1; then
        echo "✅ OK"
        return 0
    else
        echo "❌ FAILED"
        return 1
    fi
}

# Track overall health
OVERALL_STATUS=0

# Check API health endpoint
if ! check_endpoint "$API_ENDPOINT/api/health" "API Health"; then
    OVERALL_STATUS=1
fi

# Check API docs (Swagger)
if [[ "${ENABLE_SWAGGER:-true}" == "true" ]]; then
    if ! check_endpoint "$API_ENDPOINT/api/docs" "API Documentation" 3; then
        echo "  (Note: Swagger may be disabled)"
    fi
fi

# Mode-specific health checks
if [[ "$DEPLOYMENT_MODE" == "offline" ]]; then
    echo ""
    echo "🐳 Local Infrastructure Checks:"

    # Check Cosmos DB Emulator
    if ! check_endpoint "https://localhost:8081/_explorer/index.html" "Cosmos DB Emulator" 3; then
        OVERALL_STATUS=1
    fi

    # Check Azurite
    if ! check_endpoint "http://localhost:10000" "Azurite Blob Service" 2; then
        echo "  (Note: Azurite may not be running)"
    fi

    # Check RabbitMQ Management
    if ! check_endpoint "http://localhost:15672" "RabbitMQ Management" 2; then
        echo "  (Note: RabbitMQ may not be running yet)"
    fi

elif [[ "$DEPLOYMENT_MODE" == "online" ]]; then
    echo ""
    echo "☁️  Azure Service Checks:"

    # For online mode, we could add Azure-specific checks here
    # e.g., check if Storage Account is accessible, Service Bus namespace, etc.
    echo "  (Azure service checks require authentication)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ $OVERALL_STATUS -eq 0 ]]; then
    echo "✅ Health check PASSED"
    exit 0
else
    echo "❌ Health check FAILED - some services are unavailable"
    exit 1
fi