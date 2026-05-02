#!/bin/bash
set -e

# ===================================================================
# Cosmos DB Emulator Initialization Script
# ===================================================================
# This script waits for the Cosmos DB emulator to be ready, then
# creates the AzureTRE database and all required containers.
# ===================================================================

echo "🚀 Starting Cosmos DB initialization..."

# Configuration
COSMOS_ENDPOINT="${STATE_STORE_ENDPOINT:-https://cosmosdb:8081}"
COSMOS_KEY="${STATE_STORE_KEY:-C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==}"
DATABASE_NAME="${STATE_STORE_DATABASE:-AzureTRE}"

# Container definitions
declare -A CONTAINERS=(
    ["Resources"]="/id"
    ["ResourceTemplates"]="/id"
    ["ResourceHistory"]="/id"
    ["Operations"]="/id"
    ["Requests"]="/id"
    ["AirlockRequests"]="/id"
    ["AirlockRequestsHistory"]="/id"
)

# Wait for Cosmos DB emulator to be ready
echo "⏳ Waiting for Cosmos DB emulator to be ready..."
MAX_RETRIES=60
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -k -s -f "${COSMOS_ENDPOINT}/_explorer/index.html" > /dev/null 2>&1; then
        echo "✅ Cosmos DB emulator is ready!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "❌ Cosmos DB emulator failed to start after ${MAX_RETRIES} retries"
        exit 1
    fi
    
    echo "   Attempt ${RETRY_COUNT}/${MAX_RETRIES} - waiting 5 seconds..."
    sleep 5
done

# Function to create database using REST API
create_database() {
    local db_name=$1
    echo "📦 Creating database: ${db_name}"
    
    # Generate authorization token
    local verb="POST"
    local resource_type="dbs"
    local resource_link=""
    local date=$(date -u +"%a, %d %b %Y %H:%M:%S GMT")
    
    # Create the request
    local response=$(curl -k -s -w "\n%{http_code}" -X POST \
        "${COSMOS_ENDPOINT}/dbs" \
        -H "Content-Type: application/json" \
        -H "x-ms-date: ${date}" \
        -H "x-ms-version: 2018-12-31" \
        -H "Authorization: type%3Dmaster%26ver%3D1.0%26sig%3D${COSMOS_KEY}" \
        -d "{\"id\":\"${db_name}\"}")
    
    local http_code=$(echo "$response" | tail -n1)
    
    if [[ "$http_code" == "201" ]] || [[ "$http_code" == "409" ]]; then
        echo "   ✅ Database '${db_name}' ready (HTTP ${http_code})"
        return 0
    else
        echo "   ⚠️  Database creation response: HTTP ${http_code}"
        return 0  # Continue even if database already exists
    fi
}

# Function to create container using REST API
create_container() {
    local db_name=$1
    local container_name=$2
    local partition_key=$3
    
    echo "📋 Creating container: ${container_name} (partition key: ${partition_key})"
    
    local date=$(date -u +"%a, %d %b %Y %H:%M:%S GMT")
    
    # Create container definition
    local container_def=$(cat <<JSON
{
    "id": "${container_name}",
    "partitionKey": {
        "paths": ["${partition_key}"],
        "kind": "Hash"
    },
    "indexingPolicy": {
        "automatic": true,
        "indexingMode": "consistent"
    }
}
JSON
)
    
    local response=$(curl -k -s -w "\n%{http_code}" -X POST \
        "${COSMOS_ENDPOINT}/dbs/${db_name}/colls" \
        -H "Content-Type: application/json" \
        -H "x-ms-date: ${date}" \
        -H "x-ms-version: 2018-12-31" \
        -H "x-ms-offer-throughput: 400" \
        -H "Authorization: type%3Dmaster%26ver%3D1.0%26sig%3D${COSMOS_KEY}" \
        -d "${container_def}")
    
    local http_code=$(echo "$response" | tail -n1)
    
    if [[ "$http_code" == "201" ]] || [[ "$http_code" == "409" ]]; then
        echo "   ✅ Container '${container_name}' ready (HTTP ${http_code})"
    else
        echo "   ⚠️  Container creation response: HTTP ${http_code}"
    fi
}

# Create database
create_database "${DATABASE_NAME}"

echo ""
echo "📋 Creating containers..."

# Create all containers
for container in "${!CONTAINERS[@]}"; do
    partition_key="${CONTAINERS[$container]}"
    create_container "${DATABASE_NAME}" "${container}" "${partition_key}"
done

echo ""
echo "✅ Cosmos DB initialization complete!"
echo ""
echo "Database: ${DATABASE_NAME}"
echo "Endpoint: ${COSMOS_ENDPOINT}"
echo "Containers created: ${#CONTAINERS[@]}"
echo ""
echo "You can now access the Cosmos DB emulator at:"
echo "  https://localhost:8081/_explorer/index.html"
echo ""
