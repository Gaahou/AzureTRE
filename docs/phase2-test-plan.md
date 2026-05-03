# Phase 2 Test Plan: Local Message Queue

**Testing User Story:** #358  
**Feature:** #118 - F3: Local Message Queue (Phase 2)  
**Stories:** 119-124  
**Branch:** feature/phase2-message-queue  
**Last Commit:** 3eb7520566a66709f5d16dfc66d3819e18f385fe  
**Test Date:** 2026-05-03

---

## Test Environment

### Docker-Based Testing (Rule #7)
All tests executed in Docker containers to ensure reproducible results.

**Test Script:** `scripts/test_phase2_docker.sh`

**Test Image:** `azuretre-api-test:phase2` (built from `api_app/Dockerfile`)

---

## Test Scope

Phase 2 introduces local message queue infrastructure using RabbitMQ for offline mode:

### Stories Under Test

| ID | Story | Description |
|----|-------|-------------|
| 119 | Add RabbitMQ to offline docker-compose | RabbitMQ container with management UI |
| 120 | Implement RabbitMQ message bus provider | `RabbitMQMessageBus` class implementing `MessageBus` interface |
| 121 | Implement RabbitMQ event publisher provider | `RabbitMQEventPublisher` class implementing `EventPublisher` interface |
| 122 | Create local resource processor | Python service consuming messages from RabbitMQ |
| 123 | Add resource processor to offline docker-compose | Resource processor container wired to RabbitMQ |
| 124 | Wire event publishing through provider factory | Event publishing uses factory pattern for mode switching |

---

## Test Categories

### 1. Infrastructure Tests

#### 1.1 RabbitMQ Container Startup
**Story:** 119  
**Objective:** Verify RabbitMQ starts successfully in offline mode

**Test Steps:**
```bash
cd deploy/offline
docker-compose up -d rabbitmq
docker-compose ps rabbitmq
```

**Expected Results:**
- [ ] RabbitMQ container starts successfully
- [ ] Container status is "healthy"
- [ ] RabbitMQ management UI accessible at http://localhost:15672
- [ ] Default credentials work (guest/guest)
- [ ] Required exchanges created automatically

**Acceptance Criteria:**
- Container starts within 30 seconds
- Management UI responsive
- No error logs in container

---

#### 1.2 Resource Processor Container Startup
**Stories:** 122, 123  
**Objective:** Verify resource processor container starts and connects to RabbitMQ

**Test Steps:**
```bash
cd deploy/offline
docker-compose up -d resource-processor
docker-compose ps resource-processor
docker-compose logs resource-processor
```

**Expected Results:**
- [ ] Resource processor container starts successfully
- [ ] Connects to RabbitMQ successfully
- [ ] Subscribes to `tre.resource-request` queue
- [ ] Logs show "Waiting for messages..."
- [ ] No connection errors

**Acceptance Criteria:**
- Container starts within 15 seconds
- Successfully connects to RabbitMQ
- Ready to process messages

---

### 2. Message Bus Tests

#### 2.1 RabbitMQ Message Bus Provider - Basic Operations
**Story:** 120  
**Objective:** Verify `RabbitMQMessageBus` can publish and consume messages

**Test Steps:**
```python
# In Docker container
from providers.factory import get_message_bus
import asyncio

async def test_message_bus():
    message_bus = get_message_bus()
    
    # Test 1: Publish message
    await message_bus.send_message(
        message={"action": "deploy", "resource_id": "test-123"},
        routing_key="tre.resource-request"
    )
    
    # Test 2: Consume message
    async def callback(message):
        print(f"Received: {message}")
        assert message["resource_id"] == "test-123"
    
    await message_bus.subscribe(
        queue_name="tre.resource-request",
        callback=callback
    )

asyncio.run(test_message_bus())
```

**Expected Results:**
- [ ] Message published successfully
- [ ] Message received by consumer
- [ ] Message content intact (no corruption)
- [ ] Routing key honored

**Acceptance Criteria:**
- Publish completes without errors
- Consumer receives message within 1 second
- Message payload matches original

---

#### 2.2 Message Bus Provider Factory
**Story:** 120, 124  
**Objective:** Verify factory returns correct message bus based on `DEPLOYMENT_MODE`

**Test Steps:**
```python
import os
from providers.factory import get_message_bus

# Test 1: Offline mode
os.environ["DEPLOYMENT_MODE"] = "offline"
message_bus = get_message_bus()
assert message_bus.__class__.__name__ == "RabbitMQMessageBus"

# Test 2: Online mode
os.environ["DEPLOYMENT_MODE"] = "online"
message_bus = get_message_bus()
assert message_bus.__class__.__name__ == "AzureServiceBusMessageBus"
```

**Expected Results:**
- [ ] Offline mode returns `RabbitMQMessageBus`
- [ ] Online mode returns `AzureServiceBusMessageBus`
- [ ] No import errors
- [ ] Factory pattern working correctly

**Acceptance Criteria:**
- Correct implementation returned based on mode
- Both implementations follow `MessageBus` interface

---

### 3. Event Publisher Tests

#### 3.1 RabbitMQ Event Publisher - Basic Operations
**Story:** 121  
**Objective:** Verify `RabbitMQEventPublisher` can publish events to topic exchanges

**Test Steps:**
```python
# In Docker container
from providers.factory import get_event_publisher
from models.domain.events import EventGridEvent
import asyncio

async def test_event_publisher():
    event_publisher = get_event_publisher()
    
    # Test: Publish status changed event
    event = EventGridEvent(
        id="test-event-123",
        subject="workspaces/ws-001/status",
        event_type="statusChanged",
        data={"status": "deployed", "workspace_id": "ws-001"}
    )
    
    await event_publisher.publish(
        event=event,
        topic="statusChanged"
    )

asyncio.run(test_event_publisher())
```

**Expected Results:**
- [ ] Event published to RabbitMQ topic exchange
- [ ] Event routed to `tre.events.status` exchange
- [ ] Event visible in RabbitMQ management UI
- [ ] No errors during publish

**Acceptance Criteria:**
- Publish completes without errors
- Event appears in correct exchange
- Event structure preserved

---

#### 3.2 Event Publisher Provider Factory
**Story:** 121, 124  
**Objective:** Verify factory returns correct event publisher based on `DEPLOYMENT_MODE`

**Test Steps:**
```python
import os
from providers.factory import get_event_publisher

# Test 1: Offline mode
os.environ["DEPLOYMENT_MODE"] = "offline"
event_publisher = get_event_publisher()
assert event_publisher.__class__.__name__ == "RabbitMQEventPublisher"

# Test 2: Online mode
os.environ["DEPLOYMENT_MODE"] = "online"
event_publisher = get_event_publisher()
assert event_publisher.__class__.__name__ == "AzureEventGridPublisher"
```

**Expected Results:**
- [ ] Offline mode returns `RabbitMQEventPublisher`
- [ ] Online mode returns `AzureEventGridPublisher`
- [ ] No import errors
- [ ] Factory pattern working correctly

**Acceptance Criteria:**
- Correct implementation returned based on mode
- Both implementations follow `EventPublisher` interface

---

### 4. Integration Tests

#### 4.1 End-to-End Message Flow
**Stories:** 119-124  
**Objective:** Verify complete message flow from API → RabbitMQ → Resource Processor

**Test Steps:**
```bash
# 1. Start all services
cd deploy/offline
docker-compose up -d

# 2. Send message via API (simulate workspace deployment)
curl -X POST http://localhost:8000/api/workspaces \
  -H "Content-Type: application/json" \
  -d '{"template_name": "base-workspace"}'

# 3. Check resource processor logs
docker-compose logs -f resource-processor
```

**Expected Results:**
- [ ] API accepts request
- [ ] Message published to RabbitMQ
- [ ] Resource processor receives message
- [ ] Resource processor processes message
- [ ] Status updated in database
- [ ] Status changed event published

**Acceptance Criteria:**
- Complete flow completes within 5 seconds
- No errors in any component
- Message successfully processed

---

#### 4.2 Event Publishing Integration
**Story:** 124  
**Objective:** Verify event publishing through `event_grid/helpers.py` uses factory

**Test Steps:**
```python
# In Docker container
from event_grid.helpers import publish_event
from models.domain.events import EventGridEvent
import asyncio

async def test_event_helpers():
    event = EventGridEvent(
        id="integration-test-001",
        subject="test/integration",
        event_type="airlockNotification",
        data={"status": "test"}
    )
    
    # This should use factory → RabbitMQ in offline mode
    await publish_event(event, "airlockNotification")

asyncio.run(test_event_helpers())
```

**Expected Results:**
- [ ] `publish_event()` calls `get_event_publisher()`
- [ ] Factory returns `RabbitMQEventPublisher` in offline mode
- [ ] Event published to RabbitMQ
- [ ] No direct Azure Event Grid SDK calls

**Acceptance Criteria:**
- Event published via factory pattern
- No regression in online mode
- Code follows abstraction pattern

---

### 5. Resource Processor Tests

#### 5.1 Resource Processor Message Handling
**Story:** 122  
**Objective:** Verify resource processor can receive and process messages

**Test Steps:**
```bash
# 1. Send test message to queue
python3 << EOF
import asyncio
from aio_pika import connect_robust, Message

async def send_test_message():
    connection = await connect_robust("amqp://guest:guest@localhost:5672/")
    channel = await connection.channel()
    
    await channel.default_exchange.publish(
        Message(b'{"action": "deploy", "resource_id": "test-rp-001"}'),
        routing_key="tre.resource-request"
    )
    
    await connection.close()

asyncio.run(send_test_message())
EOF

# 2. Check processor logs
docker-compose logs resource-processor | tail -20
```

**Expected Results:**
- [ ] Resource processor receives message
- [ ] Logs show "Processing message: test-rp-001"
- [ ] Message acknowledged
- [ ] No processing errors

**Acceptance Criteria:**
- Message received within 2 seconds
- Processor handles message correctly
- Message removed from queue

---

### 6. Regression Tests

#### 6.1 Online Mode - No Regressions
**Stories:** 119-124  
**Objective:** Verify online mode (Azure Service Bus/Event Grid) still works

**Test Steps:**
```bash
# 1. Set online mode
export DEPLOYMENT_MODE=online

# 2. Run API in Docker
cd api_app
docker build --target test -t azuretre-api-test:phase2 .
docker run --rm \
  -e DEPLOYMENT_MODE=online \
  azuretre-api-test:phase2 \
  python -c "
from providers.factory import get_message_bus, get_event_publisher

mb = get_message_bus()
print(f'Message Bus: {mb.__class__.__name__}')
assert mb.__class__.__name__ == 'AzureServiceBusMessageBus'

ep = get_event_publisher()
print(f'Event Publisher: {ep.__class__.__name__}')
assert ep.__class__.__name__ == 'AzureEventGridPublisher'

print('✅ Online mode working correctly')
"
```

**Expected Results:**
- [ ] Online mode uses `AzureServiceBusMessageBus`
- [ ] Online mode uses `AzureEventGridPublisher`
- [ ] No import errors
- [ ] No breaking changes to Azure implementations

**Acceptance Criteria:**
- Online mode unchanged
- Azure SDK still imported correctly
- No regressions

---

### 7. Unit Tests

#### 7.1 Run Full Test Suite
**All Stories**  
**Objective:** Verify all existing unit tests pass

**Test Steps:**
```bash
# In Docker container
cd /api
pytest tests_ma/ -v --tb=short
```

**Expected Results:**
- [ ] All tests pass (100%)
- [ ] No new test failures
- [ ] No skipped tests
- [ ] Test coverage maintained or improved

**Acceptance Criteria:**
- Zero test failures
- Test suite completes within 2 minutes

---

### 8. Code Quality Tests

#### 8.1 Linting
**All Stories**  
**Objective:** Verify code follows style guidelines

**Test Steps:**
```bash
cd api_app
flake8 providers/ event_grid/ --count --max-line-length=127
```

**Expected Results:**
- [ ] No linting errors
- [ ] Code follows PEP 8 guidelines
- [ ] No unused imports

**Acceptance Criteria:**
- Zero linting errors

---

## Test Execution Checklist

- [ ] All infrastructure tests passed
- [ ] All message bus tests passed
- [ ] All event publisher tests passed
- [ ] All integration tests passed
- [ ] All resource processor tests passed
- [ ] All regression tests passed (online mode)
- [ ] All unit tests passed
- [ ] Code quality checks passed

---

## Test Results Summary

**Executed By:** [Name]  
**Execution Date:** [Date]  
**Environment:** Docker (local)  
**Commit:** 3eb7520566a66709f5d16dfc66d3819e18f385fe

### Results

| Category | Tests | Passed | Failed | Status |
|----------|-------|--------|--------|--------|
| Infrastructure | TBD | TBD | TBD | ⏳ Pending |
| Message Bus | TBD | TBD | TBD | ⏳ Pending |
| Event Publisher | TBD | TBD | TBD | ⏳ Pending |
| Integration | TBD | TBD | TBD | ⏳ Pending |
| Resource Processor | TBD | TBD | TBD | ⏳ Pending |
| Regression | TBD | TBD | TBD | ⏳ Pending |
| Unit Tests | TBD | TBD | TBD | ⏳ Pending |
| Code Quality | TBD | TBD | TBD | ⏳ Pending |

### Issues Found

[Document any issues discovered during testing]

### Recommendations

[Document any recommendations for improvements]

---

## Sign-off

- [ ] All acceptance criteria met
- [ ] All test categories completed
- [ ] Test results documented
- [ ] Issues logged (if any)
- [ ] Ready to close Phase 2 stories

**Tester Signature:** _______________  
**Date:** _______________