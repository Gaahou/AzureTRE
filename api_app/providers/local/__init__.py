"""
Local provider implementations for offline deployment mode.

This package contains implementations of the provider interfaces
for local/offline mode using open-source alternatives:
- RabbitMQ for message bus and event publishing
- Keycloak for authentication (Phase 3)
- HashiCorp Vault for secrets management (Phase 3)
"""

from providers.local.rabbitmq import RabbitMQMessageBus, RabbitMQEventPublisher
from providers.local.credentials import LocalCredentialProvider
from providers.local.secrets import LocalSecretProvider

__all__ = [
    "RabbitMQMessageBus",
    "RabbitMQEventPublisher",
    "LocalCredentialProvider",
    "LocalSecretProvider",
]
