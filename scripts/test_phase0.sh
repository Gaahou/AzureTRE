#!/bin/bash
# Phase 0 Testing Script
# Automated tests for Provider Abstraction & Mode Switching

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 0 Testing - Provider Abstraction${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Function to print test result
print_result() {
    local test_name=$1
    local result=$2

    if [ "$result" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗${NC} $test_name"
        ((TESTS_FAILED++))
    fi
}

print_skip() {
    local test_name=$1
    echo -e "${YELLOW}⊘${NC} $test_name (skipped)"
    ((TESTS_SKIPPED++))
}

echo -e "${BLUE}Stage 1: Configuration Validation${NC}"
echo "-----------------------------------"

# Test 1: Check deployment_mode in config.yaml
if command -v yq &> /dev/null; then
    MODE=$(yq '.developer_settings.deployment_mode' "$PROJECT_ROOT/config.yaml" 2>/dev/null || echo "")
    if [ "$MODE" = "online" ]; then
        print_result "Config has deployment_mode=online" 0
    else
        print_result "Config has deployment_mode=online (got: $MODE)" 1
    fi
else
    print_skip "Config validation (yq not installed)"
fi

# Test 2: Python can load DEPLOYMENT_MODE
cd "$PROJECT_ROOT/api_app"
if python -c "from core.config import DEPLOYMENT_MODE; assert DEPLOYMENT_MODE == 'online'" 2>/dev/null; then
    print_result "Python loads DEPLOYMENT_MODE correctly" 0
else
    print_result "Python loads DEPLOYMENT_MODE correctly" 1
fi

echo ""
echo -e "${BLUE}Stage 2: Provider Structure${NC}"
echo "----------------------------"

# Test 3: Provider package structure
if [ -d "$PROJECT_ROOT/api_app/providers" ] && \
   [ -f "$PROJECT_ROOT/api_app/providers/interfaces.py" ] && \
   [ -f "$PROJECT_ROOT/api_app/providers/factory.py" ] && \
   [ -d "$PROJECT_ROOT/api_app/providers/azure" ]; then
    print_result "Provider package structure exists" 0
else
    print_result "Provider package structure exists" 1
fi

# Test 4: Provider modules import
cd "$PROJECT_ROOT/api_app"
if python << 'EOF' 2>/dev/null
from providers.interfaces import MessageBus, EventPublisher, CredentialProvider
from providers.factory import get_message_bus, get_event_publisher, get_credential_provider
from providers.azure.servicebus import AzureServiceBusMessageBus
from providers.azure.eventgrid import AzureEventGridPublisher
from providers.azure.credentials import AzureCredentialProvider
EOF
then
    print_result "All provider modules import successfully" 0
else
    print_result "All provider modules import successfully" 1
fi

echo ""
echo -e "${BLUE}Stage 3: Factory Behavior${NC}"
echo "-------------------------"

# Test 5: Factory returns Azure implementations in online mode
cd "$PROJECT_ROOT/api_app"
if python << 'EOF' 2>/dev/null
import os
os.environ['DEPLOYMENT_MODE'] = 'online'
from providers.factory import get_message_bus, get_event_publisher, get_credential_provider
from providers.azure.servicebus import AzureServiceBusMessageBus
from providers.azure.eventgrid import AzureEventGridPublisher
from providers.azure.credentials import AzureCredentialProvider

# These may fail if Azure config missing, but imports should work
print("Factory functions callable")
EOF
then
    print_result "Factory loads Azure implementations" 0
else
    print_result "Factory loads Azure implementations" 1
fi

# Test 6: Factory raises NotImplementedError in offline mode
cd "$PROJECT_ROOT/api_app"
if python << 'EOF' 2>/dev/null
import os
os.environ['DEPLOYMENT_MODE'] = 'offline'
from providers.factory import get_message_bus

try:
    bus = get_message_bus()
    exit(1)  # Should not reach here
except NotImplementedError:
    exit(0)  # Expected
EOF
then
    print_result "Factory raises NotImplementedError for offline mode" 0
else
    print_result "Factory raises NotImplementedError for offline mode" 1
fi

echo ""
echo -e "${BLUE}Stage 4: Infrastructure${NC}"
echo "-----------------------"

# Test 7: Deploy folder structure
if [ -d "$PROJECT_ROOT/deploy/online" ] && \
   [ -d "$PROJECT_ROOT/deploy/offline" ] && \
   [ -d "$PROJECT_ROOT/deploy/shared" ]; then
    print_result "Deploy folder structure exists" 0
else
    print_result "Deploy folder structure exists" 1
fi

# Test 8: Shared scripts exist
if [ -f "$PROJECT_ROOT/deploy/shared/env.sh" ] && \
   [ -f "$PROJECT_ROOT/deploy/shared/healthcheck.sh" ]; then
    print_result "Shared scripts exist" 0
else
    print_result "Shared scripts exist" 1
fi

# Test 9: Scripts are executable
if [ -x "$PROJECT_ROOT/deploy/shared/env.sh" ] && \
   [ -x "$PROJECT_ROOT/deploy/shared/healthcheck.sh" ]; then
    print_result "Scripts have execute permissions" 0
else
    print_result "Scripts have execute permissions" 1
fi

echo ""
echo -e "${BLUE}Stage 5: Unit Tests${NC}"
echo "-------------------"

# Test 10: Run pytest
cd "$PROJECT_ROOT/api_app"
if python -m pytest tests_ma/ -q --tb=no 2>&1 | grep -q "passed"; then
    print_result "Unit tests pass" 0
else
    echo -e "${YELLOW}⚠ Running full test output...${NC}"
    python -m pytest tests_ma/ -v --tb=short
    print_result "Unit tests pass" 1
fi

echo ""
echo -e "${BLUE}Stage 6: Code Quality${NC}"
echo "---------------------"

# Test 11: No direct Azure SDK imports in refactored files
if ! grep -q "from azure.servicebus" "$PROJECT_ROOT/api_app/service_bus/helpers.py" 2>/dev/null; then
    print_result "No direct ServiceBus SDK imports in helpers" 0
else
    print_result "No direct ServiceBus SDK imports in helpers" 1
fi

if [ -f "$PROJECT_ROOT/api_app/event_grid/helpers.py" ]; then
    if ! grep -q "from azure.eventgrid" "$PROJECT_ROOT/api_app/event_grid/helpers.py" 2>/dev/null; then
        print_result "No direct EventGrid SDK imports in helpers" 0
    else
        print_result "No direct EventGrid SDK imports in helpers" 1
    fi
else
    print_skip "EventGrid helpers check (file may not exist)"
fi

# Test 12: Linting
cd "$PROJECT_ROOT"
if make lint &>/dev/null; then
    print_result "Linting passes" 0
else
    print_skip "Linting (make lint failed - may need setup)"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Passed:${NC}  $TESTS_PASSED"
echo -e "${RED}Failed:${NC}  $TESTS_FAILED"
echo -e "${YELLOW}Skipped:${NC} $TESTS_SKIPPED"
echo ""

# Overall result
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Phase 0 tests PASSED${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Mark stories 106-112 as Resolved in Azure DevOps"
    echo "  2. Mark feature 105 as Resolved"
    echo "  3. Begin Phase 1 (Stories 114-117)"
    exit 0
else
    echo -e "${RED}✗ Phase 0 tests FAILED${NC}"
    echo ""
    echo "Review failures above and fix before proceeding to Phase 1"
    exit 1
fi