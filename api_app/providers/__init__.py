"""
Provider abstraction layer for Azure TRE.

This package provides interface definitions and factory functions for swapping
external service implementations based on deployment mode (online/offline).

Interfaces:
- MessageBus: Message queue abstraction (Azure Service Bus / RabbitMQ)
- EventPublisher: Event publishing abstraction (Azure Event Grid / RabbitMQ Topics)
- CredentialProvider: Authentication and credential management (Azure AD / Keycloak)

Usage:
    from providers.factory import get_message_bus, get_event_publisher, get_credential_provider

    # Get provider instances based on DEPLOYMENT_MODE
    message_bus = get_message_bus()
    event_publisher = get_event_publisher()
    credential_provider = get_credential_provider()
"""

from providers.interfaces import MessageBus, EventPublisher, CredentialProvider

__all__ = ["MessageBus", "EventPublisher", "CredentialProvider"]