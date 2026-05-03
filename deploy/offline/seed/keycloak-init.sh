#!/bin/bash
# Keycloak Realm Import Script
# Imports the AzureTRE realm configuration into Keycloak using kcadm.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REALM_FILE="${SCRIPT_DIR}/AzureTRE-realm.json"

echo "🔐 Keycloak Realm Import"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Wait for Keycloak to be ready
echo "⏳ Waiting for Keycloak to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -sf http://localhost:8080 > /dev/null 2>&1; then
        echo "✓ Keycloak is ready"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Attempt $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Keycloak failed to start"
    exit 1
fi

sleep 5  # Additional wait for full initialization

# Check if realm already exists
echo ""
echo "🔍 Checking if AzureTRE realm exists..."
REALM_CHECK=$(docker exec tre-keycloak /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password admin_password 2>&1)

REALM_EXISTS=$(docker exec tre-keycloak /opt/keycloak/bin/kcadm.sh get realms/AzureTRE 2>&1 || echo "NOT_FOUND")

if [[ "$REALM_EXISTS" != *"NOT_FOUND"* ]] && [[ "$REALM_EXISTS" != *"Resource not found"* ]]; then
    echo "⚠️  Realm 'AzureTRE' already exists - skipping import"
    echo ""
    echo "📋 Realm Details:"
    echo "$REALM_EXISTS" | jq '{realm, enabled, displayName}'
    echo ""
    echo "✅ Keycloak realm is ready"
    exit 0
fi

# Import realm
echo "📥 Importing AzureTRE realm..."
if [ ! -f "$REALM_FILE" ]; then
    echo "❌ Realm file not found: $REALM_FILE"
    exit 1
fi

IMPORT_RESULT=$(docker exec tre-keycloak /opt/keycloak/bin/kcadm.sh create realms \
  -f /opt/keycloak/data/import/AzureTRE-realm.json 2>&1)

if [[ "$IMPORT_RESULT" == *"Created new realm"* ]]; then
    echo "✓ Realm imported successfully"
elif [[ "$IMPORT_RESULT" == *"already exists"* ]]; then
    echo "⚠️  Realm already exists"
else
    echo "✓ Realm import completed"
fi

# Verify realm was imported
echo ""
echo "✅ Verifying realm configuration..."
docker exec tre-keycloak /opt/keycloak/bin/kcadm.sh get realms/AzureTRE 2>&1 | jq '{realm, enabled, displayName}'

echo ""
echo "👥 Verifying users..."
docker exec tre-keycloak /opt/keycloak/bin/kcadm.sh get users -r AzureTRE 2>&1 | jq '.[] | {username, email, enabled}'

echo ""
echo "🔐 Verifying clients..."
docker exec tre-keycloak /opt/keycloak/bin/kcadm.sh get clients -r AzureTRE 2>&1 | \
  jq '.[] | select(.clientId | startswith("tre-") or . == "swagger-ui") | {clientId, enabled}'

echo ""
echo "🎭 Verifying roles..."
docker exec tre-keycloak /opt/keycloak/bin/kcadm.sh get roles -r AzureTRE 2>&1 | \
  jq '.[] | select(.name | test("Workspace|Airlock")) | {name, description}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Keycloak realm import complete!"
echo ""
echo "🌐 Keycloak Admin Console: http://localhost:8080/admin"
echo "👤 Username: admin"
echo "🔑 Password: admin_password"
echo ""
echo "📋 Test Users:"
echo "   - admin / admin_password (WorkspaceOwner, WorkspaceResearcher, AirlockManager)"
echo "   - researcher / researcher_password (WorkspaceResearcher)"
echo ""
echo "🔗 Realm: AzureTRE"
echo "   - API Client: tre-api-client (secret: tre-api-client-secret)"
echo "   - Swagger UI: swagger-ui (public)"
echo "   - UI Client: tre-ui-client (public)"
echo ""