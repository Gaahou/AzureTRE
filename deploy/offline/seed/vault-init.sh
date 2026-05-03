#!/bin/sh
# HashiCorp Vault Initialization Script
# Seeds Vault with required secrets for Azure TRE offline mode

set -e

VAULT_ADDR="${VAULT_ADDR:-http://vault:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-root-token}"

echo "🔐 HashiCorp Vault Initialization"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Wait for Vault to be ready
echo "⏳ Waiting for Vault to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if wget -q --spider "$VAULT_ADDR/v1/sys/health" 2>/dev/null; then
        echo "✓ Vault is ready"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Attempt $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Vault failed to start"
    exit 1
fi

sleep 2  # Additional wait for full initialization

echo ""
echo "📝 Seeding Vault with TRE secrets..."
echo ""

# Enable KV v2 secrets engine at secret/ (usually enabled by default in dev mode)
echo "🔧 Enabling KV v2 secrets engine..."
wget -q -O- --header "X-Vault-Token: $VAULT_TOKEN" \
    --post-data '{"type":"kv-v2"}' \
    "$VAULT_ADDR/v1/sys/mounts/secret" > /dev/null 2>&1 || echo "  KV v2 already enabled or dev mode"

# Seed example secrets for TRE
echo ""
echo "📦 Creating TRE secrets..."

# Cosmos DB connection string (for online mode reference)
wget -q -O- --header "X-Vault-Token: $VAULT_TOKEN" \
    --header "Content-Type: application/json" \
    --post-data '{"data":{"value":"AccountEndpoint=https://example.documents.azure.com:443/;AccountKey=example-key=="}}' \
    "$VAULT_ADDR/v1/secret/data/cosmosdb-connection-string" > /dev/null
echo "  ✓ cosmosdb-connection-string"

# Storage account key
wget -q -O- --header "X-Vault-Token: $VAULT_TOKEN" \
    --header "Content-Type: application/json" \
    --post-data '{"data":{"value":"example-storage-account-key"}}' \
    "$VAULT_ADDR/v1/secret/data/storage-account-key" > /dev/null
echo "  ✓ storage-account-key"

# API client secret (Keycloak client secret, already in env but for demonstration)
wget -q -O- --header "X-Vault-Token: $VAULT_TOKEN" \
    --header "Content-Type: application/json" \
    --post-data '{"data":{"value":"tre-api-client-secret"}}' \
    "$VAULT_ADDR/v1/secret/data/api-client-secret" > /dev/null
echo "  ✓ api-client-secret"

# Service Bus connection string (for reference)
wget -q -O- --header "X-Vault-Token: $VAULT_TOKEN" \
    --header "Content-Type: application/json" \
    --post-data '{"data":{"value":"Endpoint=sb://example.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=example-key"}}' \
    "$VAULT_ADDR/v1/secret/data/servicebus-connection-string" > /dev/null
echo "  ✓ servicebus-connection-string"

# Example workspace secret
wget -q -O- --header "X-Vault-Token: $VAULT_TOKEN" \
    --header "Content-Type: application/json" \
    --post-data '{"data":{"value":"example-workspace-secret-value"}}' \
    "$VAULT_ADDR/v1/secret/data/workspace-secret" > /dev/null
echo "  ✓ workspace-secret"

echo ""
echo "✅ Vault secrets seeded successfully"
echo ""
echo "🔍 Verifying secrets..."

# List all secrets
SECRETS=$(wget -q -O- --header "X-Vault-Token: $VAULT_TOKEN" \
    "$VAULT_ADDR/v1/secret/metadata?list=true" | grep -o '"keys":\[[^]]*\]' || echo "[]")
echo "   Secrets in Vault: $SECRETS"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Vault initialization complete!"
echo ""
echo "🌐 Vault UI: $VAULT_ADDR/ui"
echo "🔑 Root Token: $VAULT_TOKEN"
echo ""
echo "📋 Access secrets via:"
echo "   vault kv get secret/cosmosdb-connection-string"
echo "   OR"
echo "   curl -H \"X-Vault-Token: $VAULT_TOKEN\" $VAULT_ADDR/v1/secret/data/cosmosdb-connection-string"
echo ""