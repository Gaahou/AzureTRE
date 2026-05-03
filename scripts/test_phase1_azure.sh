#!/bin/bash
# Phase 1 Testing Script - Azure Free Tier Version
# Tests: Local API with Azure Cosmos DB Free Tier and Azurite

# Don't exit on error - we want to collect all test results
set +e

# Get absolute path to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_OUTPUT="/tmp/phase1_azure_test_output.txt"
FAILED_TESTS=0
PASSED_TESTS=0

echo "☁️  Phase 1: Local API with Azure Cosmos DB Free Tier - Test Suite"
echo "====================================================================="
echo ""
echo "Test output will be saved to: $TEST_OUTPUT"
echo "" | tee "$TEST_OUTPUT"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_section() {
    echo "" | tee -a "$TEST_OUTPUT"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" | tee -a "$TEST_OUTPUT"
    echo -e "${BLUE}$1${NC}" | tee -a "$TEST_OUTPUT"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" | tee -a "$TEST_OUTPUT"
}

# Navigate to deploy directory
cd "$PROJECT_ROOT/deploy/offline"

# Test 1: Check .env file exists
log_section "Test 1: Environment Configuration"
if [ -f ".env" ]; then
    log_pass ".env file exists"

    # Check for required variables
    if grep -q "STATE_STORE_ENDPOINT" .env && grep -q "STATE_STORE_KEY" .env; then
        log_pass "Azure Cosmos DB configuration found in .env"
    else
        log_fail "Missing Azure Cosmos DB configuration in .env"
    fi

    if grep -q "DEPLOYMENT_MODE=offline" .env; then
        log_pass "DEPLOYMENT_MODE set to offline"
    else
        log_fail "DEPLOYMENT_MODE not set to offline"
    fi
else
    log_fail ".env file not found - run scripts/setup_azure_simple.py first"
    exit 1
fi

# Test 2: Check docker-compose.yml
log_section "Test 2: Docker Compose Configuration"
if [ -f "docker-compose.yml" ]; then
    log_pass "docker-compose.yml exists"

    # Check cosmosdb service is commented out
    if grep -q "^  # cosmosdb:" docker-compose.yml || grep -q "^  #   image: mcr.microsoft.com/cosmosdb" docker-compose.yml; then
        log_pass "Cosmos DB emulator service is commented out (using Azure)"
    else
        log_info "Cosmos DB emulator service may be active (expected to use Azure)"
    fi
else
    log_fail "docker-compose.yml not found"
    exit 1
fi

# Test 3: Check Docker is running
log_section "Test 3: Docker Environment"
if docker info > /dev/null 2>&1; then
    log_pass "Docker daemon is running"
else
    log_fail "Docker daemon is not running"
    exit 1
fi

# Test 4: Start services
log_section "Test 4: Starting Services"
log_info "Starting docker-compose services..."
docker-compose up -d 2>&1 | tee -a "$TEST_OUTPUT"

if [ $? -eq 0 ]; then
    log_pass "Services started successfully"
else
    log_fail "Failed to start services"
    exit 1
fi

# Wait for services to be ready
log_info "Waiting 30 seconds for services to initialize..."
sleep 30

# Test 5: Check containers are running
log_section "Test 5: Container Status"
CONTAINERS=$(docker-compose ps --services)

for service in tre-api azurite; do
    if echo "$CONTAINERS" | grep -q "$service"; then
        if docker-compose ps "$service" | grep -q "Up"; then
            log_pass "Container $service is running"
        else
            log_fail "Container $service is not running"
        fi
    else
        log_fail "Service $service not found"
    fi
done

# Verify cosmosdb emulator is NOT running
if docker ps | grep -q "tre-cosmosdb-emulator"; then
    log_info "Local Cosmos DB emulator is running (should use Azure instead)"
else
    log_pass "Local Cosmos DB emulator not running (using Azure Free Tier)"
fi

# Test 6: Check API logs
log_section "Test 6: API Startup Logs"
API_LOGS=$(docker-compose logs tre-api 2>&1)

if echo "$API_LOGS" | grep -q "Starting Azure TRE API in OFFLINE mode"; then
    log_pass "API started in OFFLINE mode"
else
    log_fail "API did not start in OFFLINE mode"
fi

if echo "$API_LOGS" | grep -q "Service Bus disabled"; then
    log_pass "Service Bus properly disabled"
else
    log_fail "Service Bus not disabled"
fi

if echo "$API_LOGS" | grep -q "Database 'AzureTRE' found"; then
    log_pass "Connected to Azure Cosmos DB database"
else
    log_fail "Failed to connect to database"
fi

if echo "$API_LOGS" | grep -q "Container.*verified"; then
    log_pass "Cosmos DB containers verified"
else
    log_fail "Cosmos DB containers not verified"
fi

# Test 7: Test API Health Endpoint
log_section "Test 7: API Health Endpoint"
HEALTH_RESPONSE=$(curl -s -m 10 http://localhost:8000/api/health 2>&1)

if [ $? -eq 0 ] && [ -n "$HEALTH_RESPONSE" ]; then
    log_pass "Health endpoint responded"

    # Check if it's JSON
    if echo "$HEALTH_RESPONSE" | python3 -m json.tool > /dev/null 2>&1; then
        log_pass "Health endpoint returned valid JSON"

        # Check for Cosmos DB status
        if echo "$HEALTH_RESPONSE" | grep -q "Cosmos DB"; then
            if echo "$HEALTH_RESPONSE" | grep -A 1 "Cosmos DB" | grep -q "OK"; then
                log_pass "Cosmos DB status: OK"
            else
                log_fail "Cosmos DB status: Not OK"
            fi
        fi
    else
        log_info "Health endpoint returned: $HEALTH_RESPONSE"
    fi
else
    log_fail "Health endpoint did not respond"
fi

# Test 8: Test Swagger UI
log_section "Test 8: Swagger UI"
SWAGGER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/docs 2>&1)

if [ "$SWAGGER_STATUS" = "200" ]; then
    log_pass "Swagger UI is accessible (HTTP 200)"
else
    log_fail "Swagger UI returned HTTP $SWAGGER_STATUS"
fi

# Test 9: Test specific API endpoint
log_section "Test 9: API Endpoints"
WORKSPACES_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/workspaces 2>&1)

if [ "$WORKSPACES_STATUS" = "200" ] || [ "$WORKSPACES_STATUS" = "401" ]; then
    log_pass "Workspaces endpoint is reachable (HTTP $WORKSPACES_STATUS)"
else
    log_info "Workspaces endpoint returned HTTP $WORKSPACES_STATUS"
fi

# Test 10: Verify Azure Cosmos DB connection
log_section "Test 10: Azure Cosmos DB Connectivity"
if grep -q "documents.azure.com" .env; then
    COSMOS_ENDPOINT=$(grep STATE_STORE_ENDPOINT .env | cut -d'=' -f2)
    log_pass "Using Azure Cosmos DB endpoint: $COSMOS_ENDPOINT"

    # Check if it's azure endpoint
    if echo "$COSMOS_ENDPOINT" | grep -q "documents.azure.com"; then
        log_pass "Confirmed Azure Cosmos DB Free Tier usage"
    else
        log_info "Endpoint does not appear to be Azure Cosmos DB"
    fi
else
    log_info "Could not verify Azure Cosmos DB endpoint"
fi

# Test 11: Check Azurite
log_section "Test 11: Azurite Storage Emulator"
BLOB_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:10000 2>&1)

if [ "$BLOB_STATUS" != "000" ]; then
    log_pass "Azurite blob service responding"
else
    log_fail "Azurite blob service not responding"
fi

# Final Summary
log_section "Test Summary"
TOTAL_TESTS=$((PASSED_TESTS + FAILED_TESTS))
SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")

echo "" | tee -a "$TEST_OUTPUT"
echo "Total Tests: $TOTAL_TESTS" | tee -a "$TEST_OUTPUT"
echo "Passed: $PASSED_TESTS" | tee -a "$TEST_OUTPUT"
echo "Failed: $FAILED_TESTS" | tee -a "$TEST_OUTPUT"
echo "Success Rate: ${SUCCESS_RATE}%" | tee -a "$TEST_OUTPUT"
echo "" | tee -a "$TEST_OUTPUT"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" | tee -a "$TEST_OUTPUT"
    echo -e "${GREEN}✅ All tests passed! Phase 1 is working correctly.${NC}" | tee -a "$TEST_OUTPUT"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" | tee -a "$TEST_OUTPUT"
    echo "" | tee -a "$TEST_OUTPUT"
    echo "Services:" | tee -a "$TEST_OUTPUT"
    echo "  🌐 API:       http://localhost:8000/api/docs" | tee -a "$TEST_OUTPUT"
    echo "  ❤️  Health:    http://localhost:8000/api/health" | tee -a "$TEST_OUTPUT"
    echo "  📦 Azurite:   http://localhost:10000" | tee -a "$TEST_OUTPUT"
    echo "  ☁️  Cosmos DB: Azure Free Tier (Cloud)" | tee -a "$TEST_OUTPUT"
    echo "" | tee -a "$TEST_OUTPUT"
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" | tee -a "$TEST_OUTPUT"
    echo -e "${RED}❌ Some tests failed. Review output above.${NC}" | tee -a "$TEST_OUTPUT"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" | tee -a "$TEST_OUTPUT"
    echo "" | tee -a "$TEST_OUTPUT"
    exit 1
fi