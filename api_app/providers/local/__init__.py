"""
Local provider implementations for offline deployment mode.

This package contains implementations of the provider interfaces
for local/offline mode using open-source alternatives:
- RabbitMQ for message bus and event publishing
- Keycloak for authentication (Phase 3)
"""

from providers.local.rabbitmq import RabbitMQMessageBus

__all__ = ["RabbitMQMessageBus"]
