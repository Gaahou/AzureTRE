"""
Provider factory for deployment mode switching.

This module provides factory functions that return the appropriate provider
implementations based on the DEPLOYMENT_MODE configuration.

The factory pattern enables seamless switching between:
- Online mode: Azure cloud services (Service Bus, Event Grid, Azure AD)
- Offline mode: Local emulators (RabbitMQ, Keycloak) - implemented in Phase 2+

Usage:
    from providers.factory import get_message_bus, get_event_publisher, get_credential_provider

    # Get provider instances - implementation selected automatically
    message_bus = get_message_bus()
    event_publisher = get_event_publisher()
    credential_provider = get_credential_provider()

    # Use the providers without knowing which implementation
    await message_bus.send_message("workspacequeue", '{"action": "install"}')
"""

from core.config import DEPLOYMENT_MODE
from providers.interfaces import MessageBus, EventPublisher, CredentialProvider
from services.logging import logger


def get_message_bus() -> MessageBus:
    """
    Get a MessageBus provider instance based on deployment mode.

    Returns:
        MessageBus: Azure Service Bus (online) or RabbitMQ (offline)

    Raises:
        NotImplementedError: If offline mode is selected (Phase 2+)
    """
    if DEPLOYMENT_MODE == "online":
        logger.debug("Using Azure Service Bus for message bus")
        from providers.azure.servicebus import AzureServiceBusMessageBus
        return AzureServiceBusMessageBus()
    elif DEPLOYMENT_MODE == "offline":
        logger.error("Offline mode not yet implemented for MessageBus")
        raise NotImplementedError(
            "Offline mode MessageBus (RabbitMQ) will be implemented in Phase 2. "
            "For now, please use deployment_mode: online in config.yaml"
        )
    else:
        raise ValueError(f"Invalid DEPLOYMENT_MODE: {DEPLOYMENT_MODE}. Must be 'online' or 'offline'")


def get_event_publisher() -> EventPublisher:
    """
    Get an EventPublisher provider instance based on deployment mode.

    Returns:
        EventPublisher: Azure Event Grid (online) or RabbitMQ Topics (offline)

    Raises:
        NotImplementedError: If offline mode is selected (Phase 2+)
    """
    if DEPLOYMENT_MODE == "online":
        logger.debug("Using Azure Event Grid for event publishing")
        from providers.azure.eventgrid import AzureEventGridPublisher
        return AzureEventGridPublisher()
    elif DEPLOYMENT_MODE == "offline":
        logger.error("Offline mode not yet implemented for EventPublisher")
        raise NotImplementedError(
            "Offline mode EventPublisher (RabbitMQ Topics) will be implemented in Phase 2. "
            "For now, please use deployment_mode: online in config.yaml"
        )
    else:
        raise ValueError(f"Invalid DEPLOYMENT_MODE: {DEPLOYMENT_MODE}. Must be 'online' or 'offline'")


def get_credential_provider() -> CredentialProvider:
    """
    Get a CredentialProvider instance based on deployment mode.

    Returns:
        CredentialProvider: Azure AD/Managed Identity (online) or Keycloak (offline)

    Raises:
        NotImplementedError: If offline mode is selected (Phase 3+)
    """
    if DEPLOYMENT_MODE == "online":
        logger.debug("Using Azure AD/Managed Identity for credentials")
        from providers.azure.credentials import AzureCredentialProvider
        return AzureCredentialProvider()
    elif DEPLOYMENT_MODE == "offline":
        logger.error("Offline mode not yet implemented for CredentialProvider")
        raise NotImplementedError(
            "Offline mode CredentialProvider (Keycloak) will be implemented in Phase 3. "
            "For now, please use deployment_mode: online in config.yaml"
        )
    else:
        raise ValueError(f"Invalid DEPLOYMENT_MODE: {DEPLOYMENT_MODE}. Must be 'online' or 'offline'")


# Convenience exports
__all__ = [
    "get_message_bus",
    "get_event_publisher",
    "get_credential_provider",
]