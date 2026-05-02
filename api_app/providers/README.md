# Provider Abstraction Layer

This package provides interface definitions for swapping external service implementations based on deployment mode.

## Architecture

```
api_app/providers/
├── __init__.py              # Package exports
├── interfaces.py            # Abstract base classes (ABCs)
├── factory.py               # Provider factory (Story 110)
├── azure/                   # Azure implementations (Story 109)
│   ├── servicebus.py       # Azure Service Bus → MessageBus
│   ├── eventgrid.py        # Azure Event Grid → EventPublisher
│   └── credentials.py      # Azure AD/Managed Identity → CredentialProvider
└── local/                   # Local implementations (Phase 2-3)
    ├── rabbitmq.py         # RabbitMQ → MessageBus + EventPublisher
    └── credentials.py      # Keycloak OIDC → CredentialProvider
```

## Interfaces

### MessageBus

Message queue abstraction for resource deployment requests and status updates.

**Methods:**
- `send_message(queue_name, message_body, correlation_id, session_id)` - Send message to queue
- `receive_messages(queue_name, callback, max_messages)` - Receive and process messages

**Implementations:**
- **Online**: Azure Service Bus
- **Offline**: RabbitMQ (AMQP)

**Example Usage:**
```python
from providers.factory import get_message_bus

message_bus = get_message_bus()
await message_bus.send_message(
    queue_name="workspacequeue",
    message_body='{"action": "install", "resource_id": "123"}',
    correlation_id="req-456",
    session_id="workspace-789"
)
```

### EventPublisher

Event publishing abstraction for status changes and notifications.

**Methods:**
- `publish(topic_endpoint, event_type, subject, data, event_id)` - Publish event to topic

**Implementations:**
- **Online**: Azure Event Grid
- **Offline**: RabbitMQ Topic Exchange

**Example Usage:**
```python
from providers.factory import get_event_publisher

event_publisher = get_event_publisher()
await event_publisher.publish(
    topic_endpoint="status-changed",
    event_type="statusChanged",
    subject="workspace/123",
    data={"status": "deployed", "message": "Deployment complete"}
)
```

### CredentialProvider

Authentication and credential management abstraction.

**Methods:**
- `get_credential()` - Get sync credential object
- `get_credential_async()` - Get async credential object
- `get_credential_async_context()` - Get credential as async context manager
- `get_token(scopes)` - Get access token for specified scopes

**Implementations:**
- **Online**: Azure AD / Managed Identity
- **Offline**: Keycloak OIDC

**Example Usage:**
```python
from providers.factory import get_credential_provider

credential_provider = get_credential_provider()

# As context manager (recommended)
async with credential_provider.get_credential_async_context() as credential:
    client = SomeAzureClient(endpoint, credential)
    await client.do_something()

# Direct token acquisition
token = await credential_provider.get_token(["https://management.azure.com/.default"])
```

## Factory Pattern

The factory (Story 110) reads `DEPLOYMENT_MODE` from config and returns the appropriate implementation:

```python
# api_app/providers/factory.py
from core.config import DEPLOYMENT_MODE

def get_message_bus() -> MessageBus:
    if DEPLOYMENT_MODE == "online":
        from providers.azure.servicebus import AzureServiceBus
        return AzureServiceBus()
    else:  # offline
        from providers.local.rabbitmq import RabbitMQMessageBus
        return RabbitMQMessageBus()
```

## Migration Path (Story 111)

Existing code will be refactored to use the factory:

**Before:**
```python
# Direct Azure SDK usage
from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient
from core import credentials

async def send_message(message, queue):
    async with credentials.get_credential_async_context() as credential:
        service_bus_client = ServiceBusClient(config.SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE, credential)
        async with service_bus_client:
            sender = service_bus_client.get_queue_sender(queue_name=queue)
            async with sender:
                await sender.send_messages(message)
```

**After:**
```python
# Provider abstraction
from providers.factory import get_message_bus

async def send_message(message_body, queue, correlation_id=None):
    message_bus = get_message_bus()
    await message_bus.send_message(
        queue_name=queue,
        message_body=message_body,
        correlation_id=correlation_id
    )
```

## Benefits

1. **Testability**: Easy to mock providers in unit tests
2. **Flexibility**: Swap implementations without code changes
3. **Local Development**: Run TRE 100% offline with local emulators
4. **CI/CD**: Validate changes without Azure subscription
5. **Consistency**: Single interface across all deployment modes

## Status

- ✅ **Story 108**: Interfaces defined
- ⏳ **Story 109**: Azure implementations
- ⏳ **Story 110**: Factory pattern
- ⏳ **Story 111**: Refactor existing code
- ⏳ **Phase 2**: Local implementations (RabbitMQ)
- ⏳ **Phase 3**: Local auth (Keycloak)

## See Also

- [docs/quick-start-phase0.md](../../docs/quick-start-phase0.md) - Implementation guide
- [architecture_review/epic-local-tre-deployment.md](../../architecture_review/epic-local-tre-deployment.md) - Full epic