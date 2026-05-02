#!/bin/bash
set -e

# ===================================================================
# Cosmos DB Template Seed Script
# ===================================================================
# This script seeds the Cosmos DB emulator with base workspace,
# workspace service, user resource, and shared service templates.
# ===================================================================

echo "🌱 Starting template seeding..."

# Configuration
COSMOS_ENDPOINT="${STATE_STORE_ENDPOINT:-https://cosmosdb:8081}"
COSMOS_KEY="${STATE_STORE_KEY:-C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==}"
DATABASE_NAME="${STATE_STORE_DATABASE:-AzureTRE}"
CONTAINER_NAME="${STATE_STORE_RESOURCE_TEMPLATES_CONTAINER:-ResourceTemplates}"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TEMPLATES_FILE="${SCRIPT_DIR}/templates.json"

# Check if templates file exists
if [ ! -f "${TEMPLATES_FILE}" ]; then
    echo "❌ Templates file not found: ${TEMPLATES_FILE}"
    exit 1
fi

echo "📄 Loading templates from: ${TEMPLATES_FILE}"

# Function to insert a document into Cosmos DB
insert_document() {
    local doc=$1
    local doc_id=$(echo "$doc" | jq -r '.id')
    
    echo "   📝 Inserting template: ${doc_id}"
    
    local date=$(date -u +"%a, %d %b %Y %H:%M:%S GMT")
    
    local response=$(curl -k -s -w "\n%{http_code}" -X POST \
        "${COSMOS_ENDPOINT}/dbs/${DATABASE_NAME}/colls/${CONTAINER_NAME}/docs" \
        -H "Content-Type: application/json" \
        -H "x-ms-date: ${date}" \
        -H "x-ms-version: 2018-12-31" \
        -H "x-ms-documentdb-partitionkey: [\"${doc_id}\"]" \
        -H "Authorization: type%3Dmaster%26ver%3D1.0%26sig%3D${COSMOS_KEY}" \
        -d "${doc}")
    
    local http_code=$(echo "$response" | tail -n1)
    
    if [[ "$http_code" == "201" ]]; then
        echo "      ✅ Success"
        return 0
    elif [[ "$http_code" == "409" ]]; then
        echo "      ⚠️  Already exists (HTTP 409) - skipping"
        return 0
    else
        echo "      ❌ Failed (HTTP ${http_code})"
        local body=$(echo "$response" | head -n -1)
        echo "      Response: ${body}"
        return 1
    fi
}

# Check if Cosmos DB is accessible
echo "🔍 Checking Cosmos DB connectivity..."
if ! curl -k -s -f "${COSMOS_ENDPOINT}/_explorer/index.html" > /dev/null 2>&1; then
    echo "❌ Cannot connect to Cosmos DB at ${COSMOS_ENDPOINT}"
    echo "   Make sure the Cosmos DB emulator is running and initialized"
    echo "   Run: ./cosmos-init.sh"
    exit 1
fi
echo "✅ Connected to Cosmos DB"

echo ""
echo "🌱 Seeding workspace templates..."
workspace_count=$(jq '.workspaceTemplates | length' "${TEMPLATES_FILE}")
for ((i=0; i<workspace_count; i++)); do
    template=$(jq -c ".workspaceTemplates[$i]" "${TEMPLATES_FILE}")
    insert_document "$template"
done

echo ""
echo "🌱 Seeding workspace service templates..."
service_count=$(jq '.workspaceServiceTemplates | length' "${TEMPLATES_FILE}")
for ((i=0; i<service_count; i++)); do
    template=$(jq -c ".workspaceServiceTemplates[$i]" "${TEMPLATES_FILE}")
    insert_document "$template"
done

echo ""
echo "🌱 Seeding user resource templates..."
user_resource_count=$(jq '.userResourceTemplates | length' "${TEMPLATES_FILE}")
for ((i=0; i<user_resource_count; i++)); do
    template=$(jq -c ".userResourceTemplates[$i]" "${TEMPLATES_FILE}")
    insert_document "$template"
done

echo ""
echo "🌱 Seeding shared service templates..."
shared_service_count=$(jq '.sharedServiceTemplates | length' "${TEMPLATES_FILE}")
for ((i=0; i<shared_service_count; i++)); do
    template=$(jq -c ".sharedServiceTemplates[$i]" "${TEMPLATES_FILE}")
    insert_document "$template"
done

echo ""
echo "✅ Template seeding complete!"
echo ""
echo "Summary:"
echo "  Workspace templates: ${workspace_count}"
echo "  Workspace service templates: ${service_count}"
echo "  User resource templates: ${user_resource_count}"
echo "  Shared service templates: ${shared_service_count}"
echo ""
echo "Total templates: $((workspace_count + service_count + user_resource_count + shared_service_count))"
echo ""
