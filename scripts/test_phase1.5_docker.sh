#!/bin/bash
# Test Feature 1.5 (Phase 0 Prerequisites) in Docker

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🐳 Feature 1.5 Testing in Docker"
echo "Testing Phase 0 Prerequisites: Offline Mode Configuration"
echo ""

# 1. Build test image
echo "📦 Building test image..."
cd "$PROJECT_ROOT/api_app"
docker build --target test -t azuretre-api-test:phase1.5 . --quiet

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Test image built successfully"
echo ""

# 2. Run tests in container
echo "🧪 Running Feature 1.5 tests..."
echo ""

docker run --rm \
    -v "$PROJECT_ROOT:/workspace" \
    -w /api \
    azuretre-api-test:phase1.5 \
    bash -c "
        echo '=== TC1: DEPLOYMENT_MODE Configuration Validation ==='
        echo ''

        # Test 1.1: Default mode
        echo '📋 Test 1.1: Default deployment mode'
        python3 -c 'from core.config import DEPLOYMENT_MODE, VALID_DEPLOYMENT_MODES; print(f\"  ✅ Default DEPLOYMENT_MODE = {DEPLOYMENT_MODE}\"); print(f\"  ✅ Valid modes = {VALID_DEPLOYMENT_MODES}\")'
        echo ''

        # Test 1.2: Offline mode
        echo '📋 Test 1.2: Offline mode configuration'
        DEPLOYMENT_MODE=offline python3 -c 'from core.config import DEPLOYMENT_MODE; print(f\"  ✅ DEPLOYMENT_MODE = {DEPLOYMENT_MODE}\")' && echo '  ✅ Offline mode accepted'
        echo ''

        # Test 1.3: Invalid mode (should fail)
        echo '📋 Test 1.3: Invalid mode rejection'
        if DEPLOYMENT_MODE=invalid python3 -c 'from core.config import DEPLOYMENT_MODE' 2>&1 | grep -q ValueError; then
            echo '  ✅ Invalid mode rejected with ValueError'
        else
            echo '  ❌ Invalid mode not properly rejected'
            exit 1
        fi
        echo ''

        echo '=== TC2: Code Structure Verification ==='
        echo ''

        # Test 2.1: Provider files exist
        echo '📋 Test 2.1: Provider abstraction files'
        test -f providers/interfaces.py && echo '  ✅ providers/interfaces.py exists' || (echo '  ❌ Missing interfaces.py'; exit 1)
        test -f providers/factory.py && echo '  ✅ providers/factory.py exists' || (echo '  ❌ Missing factory.py'; exit 1)
        test -f providers/azure/servicebus.py && echo '  ✅ providers/azure/servicebus.py exists' || (echo '  ❌ Missing servicebus.py'; exit 1)
        echo ''

        # Test 2.2: Import tests
        echo '📋 Test 2.2: Module imports'
        python3 -c 'from core.config import DEPLOYMENT_MODE; print(\"  ✅ core.config imports successfully\")'
        python3 -c 'from services.authentication import get_current_tre_user; print(\"  ✅ services.authentication imports successfully\")'
        python3 -c 'from providers.factory import get_message_bus; print(\"  ✅ providers.factory imports successfully\")'
        echo ''

        echo '=== TC3: Service Bus Skip Logic ==='
        echo ''

        # Test 3.1: Check main.py has offline mode check
        echo '📋 Test 3.1: Service Bus skip logic in main.py'
        if grep -q 'DEPLOYMENT_MODE == \"offline\"' main.py; then
            echo '  ✅ Offline mode check found in main.py'
        else
            echo '  ❌ Offline mode check not found'
            exit 1
        fi

        if grep -q 'Service Bus disabled' main.py; then
            echo '  ✅ Service Bus disabled log message found'
        else
            echo '  ❌ Service Bus disabled message not found'
            exit 1
        fi
        echo ''

        echo '=== TC4: Authentication Bypass Logic ==='
        echo ''

        # Test 4.1: Check aad_authentication.py has offline mode check
        echo '📋 Test 4.1: Authentication bypass in aad_authentication.py'
        if grep -q 'DEPLOYMENT_MODE == \"offline\"' services/aad_authentication.py; then
            echo '  ✅ Offline mode check found in aad_authentication.py'
        else
            echo '  ❌ Offline mode check not found'
            exit 1
        fi

        if grep -q 'Authentication bypassed' services/aad_authentication.py; then
            echo '  ✅ Authentication bypass log message found'
        else
            echo '  ❌ Authentication bypass message not found'
            exit 1
        fi
        echo ''

        echo '=== Test Summary ==='
        echo '✅ All Feature 1.5 tests passed!'
        echo ''
    " 2>&1 | tee /tmp/phase1.5_test_output.txt

TEST_EXIT_CODE=${PIPESTATUS[0]}

# 3. Cleanup
echo "🧹 Cleaning up..."
docker rmi azuretre-api-test:phase1.5 --force > /dev/null 2>&1

# 4. Report results
echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ Feature 1.5 tests PASSED"
    echo ""
    echo "📝 Test output saved to: /tmp/phase1.5_test_output.txt"
    exit 0
else
    echo "❌ Feature 1.5 tests FAILED"
    echo ""
    echo "📝 Test output saved to: /tmp/phase1.5_test_output.txt"
    exit 1
fi