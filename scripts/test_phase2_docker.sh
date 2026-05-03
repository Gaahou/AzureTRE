#!/bin/bash
# Phase 2 Testing in Docker: Local Message Queue
# Testing User Story: #358
# Feature: #118 - F3: Local Message Queue (Phase 2)
# Stories: 119-124

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "╔════════════════════════════════════════════════════╗"
echo "║   Phase 2 Testing: Local Message Queue            ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "📋 Testing User Story: #358"
echo "🎯 Feature: #118 - F3: Local Message Queue (Phase 2)"
echo "📦 Stories: 119-124"
echo "🌿 Branch: feature/phase2-message-queue"
echo "📝 Commit: $(git log -1 --format='%h - %s')"
echo ""

# Test output file
TEST_OUTPUT="/tmp/phase2_test_output.txt"
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
echo "1. BUILD DOCKER TEST IMAGE"
echo "════════════════════════════════════════════════════"
echo ""

cd "$PROJECT_ROOT/api_app"

echo "📦 Building test image..."
if docker build --target test -t azuretre-api-test:phase2 . --quiet > /dev/null 2>&1; then
    echo "✅ Test image built successfully"
else
    echo "❌ Failed to build test image"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════"
echo "2. INFRASTRUCTURE TESTS"
echo "════════════════════════════════════════════════════"

# Test 2.1: Check RabbitMQ provider exists
run_test "Story 120: RabbitMQ MessageBus provider exists" \
    "docker run --rm azuretre-api-test:phase2 python -c 'from providers.local.rabbitmq import RabbitMQMessageBus; print(\"RabbitMQMessageBus imported successfully\")'"

# Test 2.2: Check RabbitMQ EventPublisher exists
run_test "Story 121: RabbitMQ EventPublisher provider exists" \
    "docker run --rm azuretre-api-test:phase2 python -c 'from providers.local.rabbitmq import RabbitMQEventPublisher; print(\"RabbitMQEventPublisher imported successfully\")'"

# Test 2.3: Check resource processor exists
run_test "Story 122: Resource processor exists" \
    "test -f '$PROJECT_ROOT/resource_processor/local_runner/runner.py'"

# Test 2.4: Check docker-compose has RabbitMQ
run_test "Story 119: docker-compose includes RabbitMQ" \
    "grep -q 'rabbitmq:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

# Test 2.5: Check docker-compose has resource processor
run_test "Story 123: docker-compose includes resource-processor" \
    "grep -q 'resource-processor:' '$PROJECT_ROOT/deploy/offline/docker-compose.yml'"

echo ""
echo "════════════════════════════════════════════════════"
echo "3. FACTORY PATTERN TESTS"
echo "════════════════════════════════════════════════════"

# Test 3.1: MessageBus factory - offline mode
run_test "Story 120: MessageBus factory returns RabbitMQ in offline mode" \
    "docker run --rm -e DEPLOYMENT_MODE=offline azuretre-api-test:phase2 python -c 'from providers.factory import get_message_bus; mb = get_message_bus(); assert mb.__class__.__name__ == \"RabbitMQMessageBus\", f\"Expected RabbitMQMessageBus, got {mb.__class__.__name__}\"; print(\"✓ Offline mode: RabbitMQMessageBus\")'"

# Test 3.2: EventPublisher factory - offline mode
run_test "Story 121: EventPublisher factory returns RabbitMQ in offline mode" \
    "docker run --rm -e DEPLOYMENT_MODE=offline azuretre-api-test:phase2 python -c 'from providers.factory import get_event_publisher; ep = get_event_publisher(); assert ep.__class__.__name__ == \"RabbitMQEventPublisher\", f\"Expected RabbitMQEventPublisher, got {ep.__class__.__name__}\"; print(\"✓ Offline mode: RabbitMQEventPublisher\")'"

# Test 3.3: MessageBus factory - online mode (regression)
run_test "Regression: MessageBus factory returns Azure in online mode" \
    "docker run --rm -e DEPLOYMENT_MODE=online azuretre-api-test:phase2 python -c 'from providers.factory import get_message_bus; mb = get_message_bus(); assert mb.__class__.__name__ == \"AzureServiceBusMessageBus\", f\"Expected AzureServiceBusMessageBus, got {mb.__class__.__name__}\"; print(\"✓ Online mode: AzureServiceBusMessageBus\")'"

# Test 3.4: EventPublisher factory - online mode (regression)
run_test "Regression: EventPublisher factory returns Azure in online mode" \
    "docker run --rm -e DEPLOYMENT_MODE=online azuretre-api-test:phase2 python -c 'from providers.factory import get_event_publisher; ep = get_event_publisher(); assert ep.__class__.__name__ == \"AzureEventGridPublisher\", f\"Expected AzureEventGridPublisher, got {ep.__class__.__name__}\"; print(\"✓ Online mode: AzureEventGridPublisher\")'"

echo ""
echo "════════════════════════════════════════════════════"
echo "4. EVENT PUBLISHING INTEGRATION"
echo "════════════════════════════════════════════════════"

# Test 4.1: Verify event_grid/helpers.py uses factory
run_test "Story 124: event_grid/helpers.py uses factory pattern" \
    "docker run --rm azuretre-api-test:phase2 python -c 'import inspect; from event_grid import helpers; source = inspect.getsource(helpers.publish_event); assert \"get_event_publisher()\" in source, \"helpers.py should call get_event_publisher()\"; print(\"✓ helpers.py uses factory pattern\")'"

# Test 4.2: Verify no direct Azure SDK imports in helpers
run_test "Story 124: No direct Azure SDK imports in helpers.py" \
    "docker run --rm azuretre-api-test:phase2 python -c 'import inspect; from event_grid import helpers; source = inspect.getsource(helpers); assert \"EventGridPublisherClient\" not in source, \"helpers.py should not directly import EventGridPublisherClient\"; print(\"✓ No direct Azure SDK imports\")'"

echo ""
echo "════════════════════════════════════════════════════"
echo "5. INTERFACE COMPLIANCE"
echo "════════════════════════════════════════════════════"

# Test 5.1: RabbitMQMessageBus implements MessageBus interface
run_test "Story 120: RabbitMQMessageBus implements MessageBus interface" \
    "docker run --rm azuretre-api-test:phase2 python -c 'from providers.local.rabbitmq import RabbitMQMessageBus; from providers.interfaces import MessageBus; mb = RabbitMQMessageBus(); assert hasattr(mb, \"send_message\"), \"Missing send_message method\"; assert hasattr(mb, \"receive_messages\"), \"Missing receive_messages method\"; print(\"✓ RabbitMQMessageBus implements MessageBus interface\")'"

# Test 5.2: RabbitMQEventPublisher implements EventPublisher interface
run_test "Story 121: RabbitMQEventPublisher implements EventPublisher interface" \
    "docker run --rm azuretre-api-test:phase2 python -c 'from providers.local.rabbitmq import RabbitMQEventPublisher; from providers.interfaces import EventPublisher; ep = RabbitMQEventPublisher(); assert hasattr(ep, \"publish\"), \"Missing publish method\"; print(\"✓ RabbitMQEventPublisher implements EventPublisher interface\")'"

echo ""
echo "════════════════════════════════════════════════════"
echo "6. UNIT TESTS"
echo "════════════════════════════════════════════════════"
echo ""

echo "🧪 Running pytest test suite..."
docker run --rm \
    -v "$PROJECT_ROOT:/workspace" \
    -w /api \
    azuretre-api-test:phase2 \
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
echo "7. CLEANUP"
echo "════════════════════════════════════════════════════"
echo ""

echo "🧹 Cleaning up Docker images..."
docker rmi azuretre-api-test:phase2 --force > /dev/null 2>&1 || true
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
    echo "   2. Add comprehensive comment to Testing Story #358"
    echo "   3. Add comments to Stories 119-124"
    echo "   4. Close Stories 119-124 (Resolved → Closed)"
    echo "   5. Close Feature #118 (Resolved → Closed)"
    echo "   6. Close Testing Story #358 (Active → Closed)"
    echo "   7. Prompt for next feature activation"
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