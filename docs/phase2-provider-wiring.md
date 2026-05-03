# Phase 2: Provider Factory Wiring Verification

This document verifies that event publishing is properly wired through the provider factory for offline mode support.

## Event Publishing Flow

```
API Routes
    ↓
event_grid/event_sender.py
    ↓ (calls)
event_grid/helpers.py::publish_event()
    ↓ (calls)
providers/factory.py::get_event_publisher()
    ↓ (returns based on DEPLOYMENT_MODE)
    ├── Online:  providers/azure/eventgrid.py::AzureEventGridPublisher
    └── Offline: providers/local/rabbitmq.py::RabbitMQEventPublisher
```

## Files Using Event Publishing

### 1. event_grid/helpers.py
**Status:** ✅ Uses factory pattern
```python
from providers.factory import get_event_publisher

async def publish_event(event: EventGridEvent, topic_endpoint: str):
    event_publisher = get_event_publisher()  # Factory call
    await event_publisher.publish(...)
```

### 2. event_grid/event_sender.py
**Status:** ✅ Uses helpers.py (which uses factory)
```python
from event_grid.helpers import publish_event

async def send_status_changed_event(airlock_request, previous_status):
    await publish_event(status_changed_event, config.EVENT_GRID_STATUS_CHANGED_TOPIC_ENDPOINT)

async def send_airlock_notification_event(airlock_request, workspace, role_assignment_details):
    await publish_event(airlock_notification, config.EVENT_GRID_AIRLOCK_NOTIFICATION_TOPIC_ENDPOINT)
```

### 3. main.py
**Status:** ✅ No event grid initialization needed
- Event publishers are created on-demand via factory
- No global EventGrid client initialization required
- Offline mode already skips Service Bus initialization

## Provider Factory Implementation

### providers/factory.py::get_event_publisher()
```python
def get_event_publisher() -> EventPublisher:
    if DEPLOYMENT_MODE == "online":
        logger.debug("Using Azure Event Grid for event publishing")
        from providers.azure.eventgrid import AzureEventGridPublisher
        return AzureEventGridPublisher()
    elif DEPLOYMENT_MODE == "offline":
        logger.debug("Using RabbitMQ topic exchanges for event publishing")
        from providers.local.rabbitmq import RabbitMQEventPublisher
        return RabbitMQEventPublisher()
```

## EventPublisher Interface Implementations

### Online Mode: providers/azure/eventgrid.py
- Uses `EventGridPublisherClient` from Azure SDK
- Publishes to Azure Event Grid topics
- Requires Azure credentials

### Offline Mode: providers/local/rabbitmq.py
- Uses `aio-pika` for RabbitMQ
- Publishes to RabbitMQ topic exchanges
- Maps Event Grid topics to RabbitMQ exchanges:
  - `statusChanged` → `tre.events.status`
  - `airlockNotification` → `tre.events.airlock`

## Verification Checklist

- [x] No direct imports of `EventGridPublisherClient` outside providers/
- [x] All event publishing goes through `event_grid/helpers.py::publish_event()`
- [x] `helpers.py` uses `get_event_publisher()` factory function
- [x] Factory returns correct implementation based on `DEPLOYMENT_MODE`
- [x] RabbitMQ EventPublisher implementation complete (Story 121)
- [x] Online mode still works (no regression)
- [x] Offline mode uses RabbitMQ (new functionality)

## Testing

### Online Mode
```bash
export DEPLOYMENT_MODE=online
# Event publishing uses Azure Event Grid
```

### Offline Mode
```bash
export DEPLOYMENT_MODE=offline
# Event publishing uses RabbitMQ topic exchanges
```

## Dependencies

### Online Mode
- `azure-eventgrid==4.22.0`
- `azure-identity==1.25.1`

### Offline Mode
- `aio-pika==9.4.3`

## Story Completion

**Story 124: Wire event publishing through provider factory**

All event publishing was already wired through the provider factory during Stories 120-121:
- Story 120: Implemented RabbitMQ MessageBus
- Story 121: Implemented RabbitMQ EventPublisher
- Factory pattern was already in place in `event_grid/helpers.py`

No additional code changes needed - verification complete! ✅