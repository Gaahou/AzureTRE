# Quick Start: Phase 0 Implementation

## Overview

All Phase 0 stories (106-112) have been moved to **Active** state and are ready for implementation.

## Phase 0: Provider Abstraction & Mode Switching

**Goal**: Introduce provider abstraction layer and deployment mode flag for online/offline switching.

**Effort**: ~2 days (17 hours total)

## Stories Status

| ID | Story | Effort | Status |
|----|-------|--------|--------|
| ✓ 106 | 1.1 - Add deployment_mode config flag | 2 hrs | **Active** |
| ✓ 107 | 1.2 - Create deploy/ folder structure | 2 hrs | **Active** |
| ✓ 108 | 1.3 - Create provider interfaces | 2 hrs | **Active** |
| ✓ 109 | 1.4 - Extract Azure implementations | 4 hrs | **Active** |
| ✓ 110 | 1.5 - Create provider factory | 1 hr | **Active** |
| ✓ 111 | 1.6 - Refactor service_bus/helpers.py | 4 hrs | **Active** |
| ✓ 112 | 1.7 - Add mode-aware Makefile targets | 2 hrs | **Active** |

## Implementation Order

### Story 106: Add deployment_mode config flag (2 hrs)

**Files to modify:**
- `config.sample.yaml` - Add `deployment_mode: online` under new `developer_settings` section
- `config_schema.json` - Add enum validation for `deployment_mode` (online, offline)
- `api_app/core/config.py` - Add `DEPLOYMENT_MODE` environment variable (default: `"online"`)

**Verification:**
```bash
# Check config validates
yq '.deployment_mode' config.yaml

# Check Python can read it
python -c "from api_app.core.config import DEPLOYMENT_MODE; print(DEPLOYMENT_MODE)"
```

### Story 107: Create deploy/ folder structure (2 hrs)

**New directories:**
```
deploy/
├── online/              # Azure cloud deployment scripts
├── offline/             # Local Docker deployment scripts
└── shared/              # Mode-agnostic scripts
    ├── env.sh          # Reads config.yaml, exports env vars
    └── healthcheck.sh  # Mode-agnostic health checks
```

**Deliverables:**
- Create directory structure
- Write `deploy/shared/env.sh` to read `config.yaml` via `yq`
- Write `deploy/shared/healthcheck.sh` for API health checks

### Story 108: Create provider interfaces (2 hrs)

**New files:**
- `api_app/providers/__init__.py`
- `api_app/providers/interfaces.py` - Abstract base classes

**Interfaces to define:**
```python
class MessageBus(ABC):
    async def send_message(self, queue_name: str, message: dict) -> None
    async def receive_messages(self, queue_name: str, callback) -> None

class EventPublisher(ABC):
    async def publish(self, topic: str, event: dict) -> None

class CredentialProvider(ABC):
    async def get_credential(self) -> Any
    async def get_token(self, scope: str) -> str
```

### Story 109: Extract Azure implementations (4 hrs)

**New files:**
- `api_app/providers/azure/__init__.py`
- `api_app/providers/azure/servicebus.py` - Implements `MessageBus`
- `api_app/providers/azure/eventgrid.py` - Implements `EventPublisher`
- `api_app/providers/azure/credentials.py` - Implements `CredentialProvider`

**Migration:**
- Move logic from `api_app/service_bus/helpers.py` → `servicebus.py`
- Extract Event Grid publishing → `eventgrid.py`
- Extract credential logic from `api_app/core/credentials.py` → `credentials.py`

### Story 110: Create provider factory (1 hr)

**New file:**
- `api_app/providers/factory.py`

**Implementation:**
```python
def get_message_bus() -> MessageBus:
    if DEPLOYMENT_MODE == "online":
        from providers.azure.servicebus import AzureServiceBus
        return AzureServiceBus()
    raise NotImplementedError("Offline mode not yet implemented")

def get_event_publisher() -> EventPublisher:
    # Similar pattern

def get_credential_provider() -> CredentialProvider:
    # Similar pattern
```

### Story 111: Refactor service_bus/helpers.py (4 hrs)

**Files to modify:**
- `api_app/service_bus/helpers.py`
- Related files in `api_app/` that use Service Bus/Event Grid directly

**Changes:**
- Replace `azure-servicebus` SDK calls → `providers.factory.get_message_bus()`
- Replace `azure-eventgrid` SDK calls → `providers.factory.get_event_publisher()`
- Verify existing unit tests still pass

**Verification:**
```bash
cd api_app
python -m pytest tests_ma/ -v -k service_bus
```

### Story 112: Add mode-aware Makefile targets (2 hrs)

**Files to modify:**
- Root `Makefile`

**New targets:**
```makefile
DEPLOYMENT_MODE ?= $(shell yq '.deployment_mode' config.yaml)

.PHONY: up
up:
ifeq ($(DEPLOYMENT_MODE),offline)
	cd deploy/offline && docker compose up -d
else
	$(MAKE) tre-deploy
endif

.PHONY: down
down:
ifeq ($(DEPLOYMENT_MODE),offline)
	cd deploy/offline && docker compose down
else
	$(MAKE) tre-stop
endif

.PHONY: status
status:
	@deploy/shared/healthcheck.sh
```

**Verification:**
```bash
make status
```

## Acceptance Criteria

After completing all 7 stories:

- [ ] `deployment_mode` field exists in `config.yaml` and validates via JSON schema
- [ ] `api_app/providers/` package exists with interfaces, factory, and Azure implementations
- [ ] Online mode works identically through new abstraction (zero behavior change)
- [ ] `make lint` passes
- [ ] Unit tests pass: `cd api_app && python -m pytest tests_ma/ -v`
- [ ] `make status` returns API health

## Next Steps

Once Phase 0 is complete, proceed to:
- **Phase 1**: Local API with Emulators (Feature 113, Stories 114-117)

## Azure DevOps Commands

### Check story status
```bash
./scripts/ado_helper.sh get 106
```

### Move story to In Progress
```bash
./scripts/ado_helper.sh update 106 "In Progress"
```

### Move story to Done
```bash
./scripts/ado_helper.sh update 106 "Done"
```

### View all Phase 0 stories
```bash
./scripts/ado_helper.sh query "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.Parent] = 105"
```
