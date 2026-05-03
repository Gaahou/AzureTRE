#!/bin/bash
# Phase 1 Testing Script (Docker-based per Rule #7)
# Tests: Local API with Cosmos DB Emulator and Azurite

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_OUTPUT="/tmp/phase1_test_output.txt"
FAILED_TESTS=0
PASSED_TESTS=0

echo "🐳 Phase 1: Local API with Emulators - Docker Test Suite"
echo "=========================================================="
echo ""
echo "Test output will be saved to: $TEST_OUTPUT"
echo "" | tee "$TEST_OUTPUT"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_test() {
    echo "$1" | tee -a "$TEST_OUTPUT"
}

log_pass() {
    echo -e "${GREEN}✅ PASS:${NC} $1" | tee -a "$TEST_OUTPUT"
    ((PASSED_TESTS++))
}

log_fail() {
    echo -e "${RED}❌ FAIL:${NC} $1" | tee -a "$TEST_OUTPUT"
    ((FAILED_TESTS++))
}

log_info() {
    echo -e "${YELLOW}ℹ️  INFO:${NC} $1" | tee -a "$TEST_OUTPUT"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test environment..."
    cd "$PROJECT_ROOT/deploy/offline"
    docker-compose down -v > /dev/null 2>&1 || true
}

# Trap exit to ensure cleanup
trap cleanup EXIT

# ============================================================================
# Test Category 1: Infrastructure Tests
# ============================================================================

log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_test "Category 1: Infrastructure Tests"
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

log_test ""
log_test "Test 1.1: Service Startup"
cd "$PROJECT_ROOT/deploy/offline"

# Clean slate
log_info "Starting from clean slate..."
docker-compose down -v > /dev/null 2>&1 || true

# Start services
log_info "Starting services..."
docker-compose up -d 2>&1 | tee -a "$TEST_OUTPUT"

# Wait for services to be healthy (max 120 seconds)
log_info "Waiting for services to become healthy (max 120s)..."
TIMEOUT=120
ELAPSED=0
ALL_HEALTHY=false

while [ $ELAPSED -lt $TIMEOUT ]; do
    COSMOSDB_STATUS=$(docker inspect --format='{{.State.Health.Status}}' tre-cosmosdb-emulator 2>/dev/null || echo "not_found")
    AZURITE_STATUS=$(docker inspect --format='{{.State.Health.Status}}' tre-azurite 2>/dev/null || echo "not_found")
    TRE_API_STATUS=$(docker inspect --format='{{.State.Health.Status}}' tre-api 2>/dev/null || echo "not_found")

    if [ "$COSMOSDB_STATUS" = "healthy" ] && [ "$AZURITE_STATUS" = "healthy" ] && [ "$TRE_API_STATUS" = "healthy" ]; then
        ALL_HEALTHY=true
        break
    fi

    sleep 5
    ((ELAPSED+=5))
    echo -n "."
done
echo ""

if [ "$ALL_HEALTHY" = true ]; then
    log_pass "All services started and healthy in ${ELAPSED}s"
    log_info "  - cosmosdb: $COSMOSDB_STATUS"
    log_info "  - azurite: $AZURITE_STATUS"
    log_info "  - tre-api: $TRE_API_STATUS"
else
    log_fail "Services did not become healthy within ${TIMEOUT}s"
    log_info "  - cosmosdb: $COSMOSDB_STATUS"
    log_info "  - azurite: $AZURITE_STATUS"
    log_info "  - tre-api: $TRE_API_STATUS"
fi

log_test ""
log_test "Test 1.2: Port Accessibility"

# Test Cosmos DB port
if curl -k -f -s https://localhost:8081/_explorer/index.html > /dev/null 2>&1; then
    log_pass "Cosmos DB port 8081 accessible"
else
    log_fail "Cosmos DB port 8081 not accessible"
fi

# Test Azurite Blob port
if curl -f -s http://localhost:10000/devstoreaccount1?comp=list > /dev/null 2>&1; then
    log_pass "Azurite Blob port 10000 accessible"
else
    log_fail "Azurite Blob port 10000 not accessible"
fi

# Test TRE API port
if curl -f -s http://localhost:8000/api/health > /dev/null 2>&1; then
    log_pass "TRE API port 8000 accessible"
else
    log_fail "TRE API port 8000 not accessible"
fi

# ============================================================================
# Test Category 2: Environment Configuration Tests
# ============================================================================

log_test ""
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_test "Category 2: Environment Configuration Tests"
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

log_test ""
log_test "Test 2.1: Deployment Mode Flag"
DEPLOYMENT_MODE=$(docker exec tre-api env | grep DEPLOYMENT_MODE || echo "not_found")

if echo "$DEPLOYMENT_MODE" | grep -q "DEPLOYMENT_MODE=offline"; then
    log_pass "DEPLOYMENT_MODE=offline is set"
else
    log_fail "DEPLOYMENT_MODE not set correctly: $DEPLOYMENT_MODE"
fi

log_test ""
log_test "Test 2.2: Cosmos DB Connection"
COSMOS_ENDPOINT=$(docker exec tre-api env | grep STATE_STORE_ENDPOINT || echo "not_found")

if echo "$COSMOS_ENDPOINT" | grep -q "https://cosmosdb:8081"; then
    log_pass "STATE_STORE_ENDPOINT points to emulator"
else
    log_fail "STATE_STORE_ENDPOINT not set correctly: $COSMOS_ENDPOINT"
fi

log_test ""
log_test "Test 2.3: Azurite Connection"
STORAGE_CONN=$(docker exec tre-api env | grep AZURE_STORAGE_CONNECTION_STRING || echo "not_found")

if echo "$STORAGE_CONN" | grep -q "devstoreaccount1"; then
    log_pass "AZURE_STORAGE_CONNECTION_STRING uses Azurite"
else
    log_fail "AZURE_STORAGE_CONNECTION_STRING not set correctly"
fi

# ============================================================================
# Test Category 3: Database Initialization Tests
# ============================================================================

log_test ""
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_test "Category 3: Database Initialization Tests"
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

log_test ""
log_test "Test 3.1: Cosmos Database Creation"
log_info "Running cosmos-init.sh..."

if bash "$PROJECT_ROOT/deploy/offline/seed/cosmos-init.sh" 2>&1 | tee -a "$TEST_OUTPUT"; then
    log_pass "Cosmos DB initialization completed"
else
    log_fail "Cosmos DB initialization failed"
fi

log_test ""
log_test "Test 3.2: Idempotent Initialization"
log_info "Running cosmos-init.sh again..."

if bash "$PROJECT_ROOT/deploy/offline/seed/cosmos-init.sh" 2>&1 | tee -a "$TEST_OUTPUT"; then
    log_pass "Cosmos DB initialization is idempotent"
else
    log_fail "Cosmos DB initialization failed on second run"
fi

log_test ""
log_test "Test 3.3: Template Seeding"
log_info "Running seed-templates.sh..."

if bash "$PROJECT_ROOT/deploy/offline/seed/seed-templates.sh" 2>&1 | tee -a "$TEST_OUTPUT"; then
    log_pass "Template seeding completed"
else
    log_fail "Template seeding failed"
fi

# ============================================================================
# Test Category 4: API Functionality Tests
# ============================================================================

log_test ""
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_test "Category 4: API Functionality Tests"
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

log_test ""
log_test "Test 4.1: Swagger UI Access"
SWAGGER_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/docs)

if [ "$SWAGGER_RESPONSE" = "200" ]; then
    log_pass "Swagger UI accessible (HTTP $SWAGGER_RESPONSE)"
else
    log_fail "Swagger UI not accessible (HTTP $SWAGGER_RESPONSE)"
fi

log_test ""
log_test "Test 4.2: Health Endpoint"
HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/health)
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health)

if [ "$HEALTH_CODE" = "200" ]; then
    log_pass "Health endpoint returns 200"
    log_info "  Response: $HEALTH_RESPONSE"
else
    log_fail "Health endpoint returned $HEALTH_CODE"
fi

log_test ""
log_test "Test 4.3: Swagger JSON Endpoint"
SWAGGER_JSON=$(curl -s http://localhost:8000/api/openapi.json)
SWAGGER_JSON_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/openapi.json)

if [ "$SWAGGER_JSON_CODE" = "200" ] && echo "$SWAGGER_JSON" | grep -q "openapi"; then
    log_pass "OpenAPI spec accessible"
else
    log_fail "OpenAPI spec not accessible (HTTP $SWAGGER_JSON_CODE)"
fi

# ============================================================================
# Test Category 5: Cosmos DB Emulator Tests
# ============================================================================

log_test ""
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_test "Category 5: Cosmos DB Emulator Tests"
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

log_test ""
log_test "Test 5.1: Data Explorer Access"
EXPLORER_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost:10250/_explorer/index.html)

if [ "$EXPLORER_CODE" = "200" ] || [ "$EXPLORER_CODE" = "302" ]; then
    log_pass "Cosmos Data Explorer accessible (HTTP $EXPLORER_CODE)"
else
    log_fail "Cosmos Data Explorer not accessible (HTTP $EXPLORER_CODE)"
fi

log_test ""
log_test "Test 5.2: Cosmos REST API Access"
COSMOS_KEY="C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="

# Try to list databases (simple validation)
if curl -k -s -H "x-ms-version: 2018-12-31" https://localhost:8081/dbs > /dev/null 2>&1; then
    log_pass "Cosmos REST API accessible"
else
    log_fail "Cosmos REST API not accessible"
fi

# ============================================================================
# Test Category 6: Documentation Tests
# ============================================================================

log_test ""
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_test "Category 6: Documentation Tests"
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

log_test ""
log_test "Test 6.1: Required Files Exist"

FILES=(
    "deploy/offline/docker-compose.yml"
    "deploy/offline/.env.sample"
    "deploy/offline/.gitignore"
    "deploy/offline/README.md"
    "deploy/offline/seed/cosmos-init.sh"
    "deploy/offline/seed/seed-templates.sh"
    "deploy/offline/seed/templates.json"
    "deploy/offline/seed/README.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        log_pass "File exists: $file"
    else
        log_fail "File missing: $file"
    fi
done

# ============================================================================
# Final Report
# ============================================================================

log_test ""
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_test "Test Summary"
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_test ""
log_test "Total Passed: $PASSED_TESTS"
log_test "Total Failed: $FAILED_TESTS"
log_test ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Phase 1 Tests PASSED - All tests successful!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "" | tee -a "$TEST_OUTPUT"
    echo "Phase 1 is ready to move from Resolved to Closed." | tee -a "$TEST_OUTPUT"
    echo "" | tee -a "$TEST_OUTPUT"
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ Phase 1 Tests FAILED - $FAILED_TESTS test(s) failed${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "" | tee -a "$TEST_OUTPUT"
    echo "Please review test output above and fix failures." | tee -a "$TEST_OUTPUT"
    echo "" | tee -a "$TEST_OUTPUT"
    exit 1
fi