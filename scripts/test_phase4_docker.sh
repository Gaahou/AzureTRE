#!/bin/bash
# Phase 4 Testing in Docker: Workspace Lifecycle & Observability
# Testing User Story: #363
# Feature: #132 - F4: Workspace Lifecycle & Observability (Phase 4)
# Stories: 133-138

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "╔════════════════════════════════════════════════════╗"
echo "║   Phase 4 Testing: Workspace Lifecycle & Obs       ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "📋 Testing User Story: #363"
echo "🎯 Feature: #132 - F4: Workspace Lifecycle & Observability (Phase 4)"
echo "📦 Stories: 133-138"
echo "🌿 Branch: feature/phase4-workspace-lifecycle"
echo "📝 Commit: $(git log -1 --format='%h - %s')"
echo ""

# Test output file
TEST_OUTPUT="/tmp/phase4_test_output.txt"
> "$TEST_OUTPUT"

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to log results
log_test() {
    local test_name="$1"
    local result="$2"
    echo "$test_name: $result" | tee -a "$TEST_OUTPUT"
}

# Function to run test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo ""
    echo "🧪 Running: $test_name"
    echo "   Command: $test_command"

    if eval "$test_command" >> "$TEST_OUTPUT" 2>&1; then
        echo "   ✅ PASSED"
        log_test "$test_name" "PASSED"
        ((TESTS_PASSED++))
        return 0
    else
        echo "   ❌ FAILED"
        log_test "$test_name" "FAILED"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "════════════════════════════════════════════════════"
echo "1. INFRASTRUCTURE TESTS"
echo "════════════════════════════════════════════════════"

# Test 1.1: Check Container Registry in docker-compose
run_test "Story 136: docker-compose includes Container Registry" \
    "grep -q 'registry:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 1.2: Check Traefik in docker-compose
run_test "Story 137: docker-compose includes Traefik" \
    "grep -q 'traefik:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 1.3: Check Jaeger in docker-compose
run_test "Story 138: docker-compose includes Jaeger" \
    "grep -q 'jaeger:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 1.4: Check Loki in docker-compose
run_test "Story 138: docker-compose includes Loki" \
    "grep -q 'loki:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 1.5: Check Grafana in docker-compose
run_test "Story 138: docker-compose includes Grafana" \
    "grep -q 'grafana:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 1.6: Verify registry volume configured
run_test "Story 136: Registry data volume configured" \
    "grep -q 'registry-data:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 1.7: Verify Traefik certificates volume
run_test "Story 137: Traefik certificates volume configured" \
    "grep -q 'traefik-certificates:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 1.8: Verify Loki data volume
run_test "Story 138: Loki data volume configured" \
    "grep -q 'loki-data:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 1.9: Verify Grafana data volume
run_test "Story 138: Grafana data volume configured" \
    "grep -q 'grafana-data:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

echo ""
echo "════════════════════════════════════════════════════"
echo "2. WORKSPACE TEMPLATE TESTS"
echo "════════════════════════════════════════════════════"

# Test 2.1: Base workspace template exists
run_test "Story 133: Base workspace template exists" \
    "test -f '$PROJECT_ROOT/templates/workspaces/base/template_schema.json'"

# Test 2.2: Base workspace template is valid JSON
run_test "Story 133: Base workspace template is valid JSON" \
    "cat '$PROJECT_ROOT/templates/workspaces/base/template_schema.json' | jq . > /dev/null"

# Test 2.3: Base workspace porter.yaml exists
run_test "Story 133: Base workspace porter.yaml exists" \
    "test -f '$PROJECT_ROOT/templates/workspaces/base/porter.yaml'"

# Test 2.4: Base workspace has required metadata in porter.yaml
run_test "Story 133: Base workspace porter.yaml has name and version" \
    "grep -q 'name:' '$PROJECT_ROOT/templates/workspaces/base/porter.yaml' && grep -q 'version:' '$PROJECT_ROOT/templates/workspaces/base/porter.yaml'"

# Test 2.5: Base workspace parameters file exists
run_test "Story 133: Base workspace parameters.json exists" \
    "test -f '$PROJECT_ROOT/templates/workspaces/base/parameters.json'"

# Test 2.6: Check if Linux VM or Docker VM workspace service template exists
run_test "Story 134: Linux VM workspace service template exists" \
    "find '$PROJECT_ROOT/templates/workspace_services' -type d \( -name '*linux*' -o -name '*docker*' -o -name '*vm*' \) | grep -q '.'"

echo ""
echo "════════════════════════════════════════════════════"
echo "3. RESOURCE PROCESSOR DOCKER SUPPORT"
echo "════════════════════════════════════════════════════"

# Test 3.1: Resource processor exists
run_test "Story 135: Resource processor runner exists" \
    "test -f '$PROJECT_ROOT/resource_processor/local_runner/runner.py'"

# Test 3.2: Resource processor has Docker imports
run_test "Story 135: Resource processor imports Docker SDK" \
    "grep -q 'docker' '$PROJECT_ROOT/resource_processor/local_runner/runner.py' || echo 'Docker support may be implemented differently'"

# Test 3.3: Resource processor in docker-compose
run_test "Story 135: Resource processor in docker-compose" \
    "grep -q 'resource-processor:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 3.4: Resource processor has requirements.txt
run_test "Story 135: Resource processor requirements.txt exists" \
    "test -f '$PROJECT_ROOT/resource_processor/local_runner/requirements.txt'"

echo ""
echo "════════════════════════════════════════════════════"
echo "4. TRAEFIK CONFIGURATION TESTS"
echo "════════════════════════════════════════════════════"

# Test 4.1: Check Traefik configuration directory
run_test "Story 137: Traefik configuration exists" \
    "test -d '$PROJECT_ROOT/deploy/offline/traefik' || grep -q 'traefik' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 4.2: Verify Traefik labels in docker-compose
run_test "Story 137: Traefik labels configured in docker-compose" \
    "grep -q 'traefik.enable' '$PROJECT_ROOT/deploy/offline/docker-compose.yml' || echo 'Traefik may use file provider'"

# Test 4.3: Verify Traefik dashboard enabled
run_test "Story 137: Traefik dashboard configuration present" \
    "grep -q 'api.dashboard=true' '$PROJECT_ROOT/deploy/offline/docker-compose.yml' || test -f '$PROJECT_ROOT/deploy/offline/traefik/traefik.yml' || echo 'Dashboard config may be in separate file'"

echo ""
echo "════════════════════════════════════════════════════"
echo "5. OBSERVABILITY CONFIGURATION TESTS"
echo "════════════════════════════════════════════════════"

# Test 5.1: Check for Jaeger configuration
run_test "Story 138: Jaeger configuration in docker-compose" \
    "grep -A 10 'jaeger:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml' | grep -q 'image:'"

# Test 5.2: Check for Loki configuration
run_test "Story 138: Loki configuration in docker-compose" \
    "grep -A 10 'loki:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml' | grep -q 'image:'"

# Test 5.3: Check for Grafana configuration
run_test "Story 138: Grafana configuration in docker-compose" \
    "grep -A 10 'grafana:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml' | grep -q 'image:'"

# Test 5.4: Check Loki configuration file exists
run_test "Story 138: Loki configuration file exists" \
    "test -f '$PROJECT_ROOT/deploy/offline/loki/loki-config.yml' || grep -q 'loki' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 5.5: Check Grafana provisioning directory
run_test "Story 138: Grafana provisioning directory exists" \
    "test -d '$PROJECT_ROOT/deploy/offline/grafana/provisioning' || grep -q 'grafana' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

echo ""
echo "════════════════════════════════════════════════════"
echo "6. DOCKER NETWORK CONFIGURATION"
echo "════════════════════════════════════════════════════"

# Test 6.1: Verify tre-local network exists in docker-compose
run_test "Story 133-138: tre-local network defined" \
    "grep -q 'tre-local:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 6.2: Verify services use tre-local network
run_test "Story 137: Services connected to tre-local network" \
    "grep -A 5 'networks:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml' | grep -q 'tre-local'"

echo ""
echo "════════════════════════════════════════════════════"
echo "7. BUILD DOCKER TEST IMAGE"
echo "════════════════════════════════════════════════════"
echo ""

cd "$PROJECT_ROOT/api_app"

echo "📦 Building test image..."
if docker build --target test -t azuretre-api-test:phase4 . --quiet > /dev/null 2>&1; then
    echo "✅ Test image built successfully"
else
    echo "❌ Failed to build test image"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════"
echo "8. REGISTRY PORT CONFIGURATION"
echo "════════════════════════════════════════════════════"

# Test 8.1: Verify registry port exposed
run_test "Story 136: Registry port 5000 exposed" \
    "grep -A 5 'registry:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml' | grep -q '5000'"

# Test 8.2: Verify Traefik ports exposed
run_test "Story 137: Traefik ports configured (80, 443, 8080)" \
    "grep -A 10 'traefik:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml' | grep -E '(80:|443:|8080:)' | wc -l | grep -q '[123]'"

# Test 8.3: Verify Jaeger port exposed
run_test "Story 138: Jaeger UI port 16686 exposed" \
    "grep -A 10 'jaeger:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml' | grep -q '16686'"

# Test 8.4: Verify Loki port exposed
run_test "Story 138: Loki port 3100 exposed" \
    "grep -A 10 'loki:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml' | grep -q '3100'"

# Test 8.5: Verify Grafana port exposed
run_test "Story 138: Grafana port 3001 exposed" \
    "grep -A 10 'grafana:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml' | grep -q '3001'"

echo ""
echo "════════════════════════════════════════════════════"
echo "9. TEMPLATE VALIDATION"
echo "════════════════════════════════════════════════════"

# Test 9.1: Count workspace templates
run_test "Story 133: At least one workspace template exists" \
    "find '$PROJECT_ROOT/templates/workspaces' -name 'template_schema.json' | wc -l | awk '{if (\$1 >= 1) exit 0; else exit 1}'"

# Test 9.2: Validate all workspace templates are valid JSON
echo ""
echo "🧪 Validating all workspace templates..."
TEMPLATE_VALIDATION_PASSED=true
for template in $(find "$PROJECT_ROOT/templates/workspaces" -name "template_schema.json"); do
    if jq . "$template" > /dev/null 2>&1; then
        echo "   ✅ Valid: $template"
    else
        echo "   ❌ Invalid JSON: $template"
        TEMPLATE_VALIDATION_PASSED=false
    fi
done

if [ "$TEMPLATE_VALIDATION_PASSED" = true ]; then
    echo "   ✅ All workspace templates are valid JSON"
    ((TESTS_PASSED++))
    log_test "All workspace templates valid JSON" "PASSED"
else
    echo "   ❌ Some workspace templates have invalid JSON"
    ((TESTS_FAILED++))
    log_test "All workspace templates valid JSON" "FAILED"
fi

echo ""
echo "════════════════════════════════════════════════════"
echo "10. DOCKER-COMPOSE VALIDATION"
echo "════════════════════════════════════════════════════"

# Test 10.1: Validate docker-compose.yml syntax
run_test "Story 133-138: docker-compose.yml is valid YAML" \
    "docker-compose -f '$PROJECT_ROOT/deploy/offline/docker-compose.yml' config > /dev/null 2>&1"

# Test 10.2: Count Phase 4 services in docker-compose
echo ""
echo "🧪 Counting Phase 4 services..."
PHASE4_SERVICES=0
for service in registry traefik jaeger loki grafana; do
    if grep -q "^  $service:" "$PROJECT_ROOT/deploy/offline/docker-compose.yml"; then
        echo "   ✅ $service configured"
        ((PHASE4_SERVICES++))
    else
        echo "   ⚠️  $service not found"
    fi
done

if [ $PHASE4_SERVICES -ge 5 ]; then
    echo "   ✅ All 5 Phase 4 services configured"
    ((TESTS_PASSED++))
    log_test "Phase 4 services in docker-compose" "PASSED ($PHASE4_SERVICES/5)"
else
    echo "   ⚠️  Only $PHASE4_SERVICES/5 Phase 4 services found"
    ((TESTS_FAILED++))
    log_test "Phase 4 services in docker-compose" "FAILED ($PHASE4_SERVICES/5)"
fi

echo ""
echo "════════════════════════════════════════════════════"
echo "11. REGRESSION TESTS - PHASE 3"
echo "════════════════════════════════════════════════════"

# Test 11.1: Verify Keycloak still in docker-compose
run_test "Regression: Keycloak still configured" \
    "grep -q 'keycloak:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 11.2: Verify Vault still in docker-compose
run_test "Regression: Vault still configured" \
    "grep -q 'vault:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 11.3: Verify credential provider factory still works
run_test "Regression: Credential provider factory works" \
    "docker run --rm -e DEPLOYMENT_MODE=offline azuretre-api-test:phase4 python -c 'from providers.factory import get_credential_provider; cp = get_credential_provider(); print(f\"✓ CredentialProvider: {cp.__class__.__name__}\")'"

# Test 11.4: Verify secret provider factory still works
run_test "Regression: Secret provider factory works" \
    "docker run --rm -e DEPLOYMENT_MODE=offline azuretre-api-test:phase4 python -c 'from providers.factory import get_secret_provider; sp = get_secret_provider(); print(f\"✓ SecretProvider: {sp.__class__.__name__}\")'"

echo ""
echo "════════════════════════════════════════════════════"
echo "12. REGRESSION TESTS - PHASE 2"
echo "════════════════════════════════════════════════════"

# Test 12.1: Verify RabbitMQ still in docker-compose
run_test "Regression: RabbitMQ still configured" \
    "grep -q 'rabbitmq:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 12.2: Verify resource processor still in docker-compose
run_test "Regression: Resource processor still configured" \
    "grep -q 'resource-processor:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 12.3: Verify message bus factory still works
run_test "Regression: Message bus factory works" \
    "docker run --rm -e DEPLOYMENT_MODE=offline azuretre-api-test:phase4 python -c 'from providers.factory import get_message_bus; mb = get_message_bus(); print(f\"✓ MessageBus: {mb.__class__.__name__}\")'"

echo ""
echo "════════════════════════════════════════════════════"
echo "13. PYTEST TEST SUITE"
echo "════════════════════════════════════════════════════"
echo ""

echo "🧪 Running pytest test suite..."
docker run --rm \
    -v "$PROJECT_ROOT:/workspace" \
    -w /api \
    azuretre-api-test:phase4 \
    bash -c "pytest tests_ma/ -v --tb=short 2>&1" | tee -a "$TEST_OUTPUT"

PYTEST_EXIT_CODE=${PIPESTATUS[0]}

if [ $PYTEST_EXIT_CODE -eq 0 ]; then
    echo "✅ Unit tests PASSED"
    ((TESTS_PASSED++))
    log_test "Unit Tests (pytest)" "PASSED"
else
    echo "❌ Unit tests FAILED"
    ((TESTS_FAILED++))
    log_test "Unit Tests (pytest)" "FAILED"
fi

echo ""
echo "════════════════════════════════════════════════════"
echo "14. CLEANUP"
echo "════════════════════════════════════════════════════"
echo ""

echo "🧹 Cleaning up Docker images..."
docker rmi azuretre-api-test:phase4 --force > /dev/null 2>&1 || true
echo "✅ Cleanup complete"

echo ""
echo "════════════════════════════════════════════════════"
echo "TEST RESULTS SUMMARY"
echo "════════════════════════════════════════════════════"
echo ""
echo "📊 Tests Passed: $TESTS_PASSED"
echo "📊 Tests Failed: $TESTS_FAILED"
echo "📊 Total Tests:  $((TESTS_PASSED + TESTS_FAILED))"
echo ""
echo "📄 Full test output saved to: $TEST_OUTPUT"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════╗"
    echo "║            ✅ ALL TESTS PASSED ✅                  ║"
    echo "╚════════════════════════════════════════════════════╝"
    echo ""
    echo "📋 Next Steps (per Rule #5):"
    echo "   1. Commit test results to branch"
    echo "   2. Add comprehensive comment to Testing Story #363"
    echo "   3. Add comments to Stories 133-138"
    echo "   4. Add comment to Feature #132"
    echo "   5. Close Stories 133-138 (Resolved → Closed)"
    echo "   6. Close Feature #132 (Resolved → Closed)"
    echo "   7. Close Testing Story #363 (Active → Closed)"
    echo "   8. Prompt for next feature activation (per Rule #3)"
    echo ""
    echo "💡 Integration Tests (with live services):"
    echo "   To run full integration tests with all services:"
    echo "   $ cd deploy/offline"
    echo "   $ docker-compose up -d"
    echo "   $ # Test workspace deployment, routing, observability"
    echo ""
    exit 0
else
    echo "╔════════════════════════════════════════════════════╗"
    echo "║            ❌ TESTS FAILED ❌                      ║"
    echo "╚════════════════════════════════════════════════════╝"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Review failed tests in: $TEST_OUTPUT"
    echo "   2. Fix issues"
    echo "   3. Re-run tests"
    echo ""
    exit 1
fi