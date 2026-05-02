# Phase 0 Testing Plan

Quick reference for testing Phase 0 implementation (Stories 106-112).

## Quick Test Run (~15 minutes)

```bash
cd /Users/andrew/Desktop/PoC/AzureTRE

# 1. Configuration check
yq '.developer_settings.deployment_mode' config.yaml
python -c "from api_app.core.config import DEPLOYMENT_MODE; print(DEPLOYMENT_MODE)"

# 2. Provider structure check
ls api_app/providers/
ls api_app/providers/azure/

# 3. Run unit tests
cd api_app && python -m pytest tests_ma/ -v --tb=short

# 4. Run linting
cd .. && make lint

# 5. Check deploy structure
ls deploy/online/ deploy/offline/ deploy/shared/

# 6. Test scripts
./deploy/shared/healthcheck.sh
```

## Acceptance Criteria Checklist

From [quick-start-phase0.md](quick-start-phase0.md):

- [ ] **AC1**: `deployment_mode` exists in config.yaml and validates
- [ ] **AC2**: `api_app/providers/` package exists with interfaces, factory, and Azure implementations
- [ ] **AC3**: Online mode works identically (no regressions)
- [ ] **AC4**: `make lint` passes
- [ ] **AC5**: Unit tests pass: `cd api_app && python -m pytest tests_ma/ -v`
- [ ] **AC6**: `make status` returns API health

## Detailed Test Stages

### Stage 1: Verify Configuration (2 min)

```bash
# Check config.yaml
yq '.developer_settings.deployment_mode' config.yaml
# Expected: online

# Check Python loads it
cd api_app
python -c "from core.config import DEPLOYMENT_MODE; print(f'Mode: {DEPLOYMENT_MODE}')"
# Expected: Mode: online
```

### Stage 2: Verify Provider Structure (2 min)

```bash
cd /Users/andrew/Desktop/PoC/AzureTRE/api_app

# Test imports
python << 'EOF'
from providers.interfaces import MessageBus, EventPublisher, CredentialProvider
from providers.factory import get_message_bus, get_event_publisher, get_credential_provider
from providers.azure.servicebus import AzureServiceBusMessageBus
from providers.azure.eventgrid import AzureEventGridPublisher
from providers.azure.credentials import AzureCredentialProvider
print("✓ All provider modules imported successfully")
EOF
```

### Stage 3: Run Unit Tests (5 min)

```bash
cd /Users/andrew/Desktop/PoC/AzureTRE/api_app

# Run full test suite
python -m pytest tests_ma/ -v --tb=short

# Or run specific areas
python -m pytest tests_ma/ -k "service_bus or event" -v
```

### Stage 4: Verify Infrastructure (3 min)

```bash
cd /Users/andrew/Desktop/PoC/AzureTRE

# Check deploy folders
ls -la deploy/online/ deploy/offline/ deploy/shared/

# Test environment script
source deploy/shared/env.sh
echo "DEPLOYMENT_MODE=$DEPLOYMENT_MODE"

# Test healthcheck (may fail if API not running - OK)
./deploy/shared/healthcheck.sh
```

### Stage 5: Code Quality (3 min)

```bash
cd /Users/andrew/Desktop/PoC/AzureTRE

# Run linting
make lint

# Check for direct Azure SDK imports (should be none)
grep -r "from azure.servicebus" api_app/service_bus/helpers.py || echo "✓ No direct imports"
grep -r "from azure.eventgrid" api_app/event_grid/helpers.py || echo "✓ No direct imports"
```

## Test Factory Behavior

```bash
cd /Users/andrew/Desktop/PoC/AzureTRE/api_app

# Test online mode (returns Azure implementations)
python << 'EOF'
import os
os.environ['DEPLOYMENT_MODE'] = 'online'
from providers.factory import get_message_bus
try:
    bus = get_message_bus()
    print(f"✓ Online mode: {type(bus).__name__}")
except Exception as e:
    print(f"⚠ May need Azure config: {e}")
EOF

# Test offline mode (raises NotImplementedError)
python << 'EOF'
import os
os.environ['DEPLOYMENT_MODE'] = 'offline'
from providers.factory import get_message_bus
try:
    bus = get_message_bus()
    print("✗ Should have raised NotImplementedError")
except NotImplementedError:
    print("✓ Correctly raises NotImplementedError for offline mode")
EOF
```

## Expected Results

**All tests pass**:
- Configuration loads correctly ✓
- All provider modules import ✓
- Unit tests pass (0 failures) ✓
- Linting passes ✓
- Deploy structure exists ✓
- Factory routes correctly ✓

## If Tests Fail

1. **Import errors**: Check `pip install -r api_app/requirements.txt`
2. **Test failures**: Review error output, check git diff for changes
3. **Lint errors**: Run `black api_app/providers/` to auto-fix
4. **Factory errors**: Verify `DEPLOYMENT_MODE` environment variable

## Next Steps

### When all tests pass:

```bash
# Mark stories complete
./scripts/ado_helper.sh update 106 "Resolved"
./scripts/ado_helper.sh update 107 "Resolved"
./scripts/ado_helper.sh update 108 "Resolved"
./scripts/ado_helper.sh update 109 "Resolved"
./scripts/ado_helper.sh update 110 "Resolved"
./scripts/ado_helper.sh update 111 "Resolved"
./scripts/ado_helper.sh update 112 "Resolved"

# Mark feature complete
./scripts/ado_helper.sh update 105 "Resolved"

# Begin Phase 1
# See docs/quick-start-phase0.md for Phase 1 stories
```

## Test Report

```
Date: 2026-05-02
Branch: feature/phase1-local-api
Commit: $(git rev-parse HEAD)

Acceptance Criteria: [ ] 6/6 passed

Stage 1 - Configuration: [ ] PASS
Stage 2 - Provider Structure: [ ] PASS
Stage 3 - Unit Tests: [ ] PASS
Stage 4 - Infrastructure: [ ] PASS
Stage 5 - Code Quality: [ ] PASS

Overall: [ ] READY FOR PHASE 1
```