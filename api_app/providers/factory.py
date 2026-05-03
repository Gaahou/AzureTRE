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
from providers.interfaces import MessageBus, EventPublisher, CredentialProvider, SecretProvider
from services.logging import logger


def get_message_bus() -> MessageBus:
    """
    Get a MessageBus provider instance based on deployment mode.

    Returns:
        MessageBus: Azure Service Bus (online) or RabbitMQ (offline)
    """
    if DEPLOYMENT_MODE == "online":
        logger.debug("Using Azure Service Bus for message bus")
        from providers.azure.servicebus import AzureServiceBusMessageBus
        return AzureServiceBusMessageBus()
    elif DEPLOYMENT_MODE == "offline":
        logger.debug("Using RabbitMQ for message bus")
        from providers.local.rabbitmq import RabbitMQMessageBus
        return RabbitMQMessageBus()
    else:
        raise ValueError(f"Invalid DEPLOYMENT_MODE: {DEPLOYMENT_MODE}. Must be 'online' or 'offline'")


def get_event_publisher() -> EventPublisher:
    """
    Get an EventPublisher provider instance based on deployment mode.

    Returns:
        EventPublisher: Azure Event Grid (online) or RabbitMQ Topics (offline)
    """
    if DEPLOYMENT_MODE == "online":
        logger.debug("Using Azure Event Grid for event publishing")
        from providers.azure.eventgrid import AzureEventGridPublisher
        return AzureEventGridPublisher()
    elif DEPLOYMENT_MODE == "offline":
        logger.debug("Using RabbitMQ topic exchanges for event publishing")
        from providers.local.rabbitmq import RabbitMQEventPublisher
        return RabbitMQEventPublisher()
    else:
        raise ValueError(f"Invalid DEPLOYMENT_MODE: {DEPLOYMENT_MODE}. Must be 'online' or 'offline'")


def get_credential_provider() -> CredentialProvider:
    """
    Get a CredentialProvider instance based on deployment mode.

    Returns:
        CredentialProvider: Azure AD/Managed Identity (online) or Keycloak (offline)
    """
    if DEPLOYMENT_MODE == "online":
        logger.debug("Using Azure AD/Managed Identity for credentials")
        from providers.azure.credentials import AzureCredentialProvider
        return AzureCredentialProvider()
    elif DEPLOYMENT_MODE == "offline":
        logger.debug("Using Keycloak OIDC for credentials")
        from providers.local.credentials import LocalCredentialProvider
        return LocalCredentialProvider()
    else:
        raise ValueError(f"Invalid DEPLOYMENT_MODE: {DEPLOYMENT_MODE}. Must be 'online' or 'offline'")


def get_secret_provider() -> SecretProvider:
    """
    Get a SecretProvider instance based on deployment mode.

    Returns:
        SecretProvider: Azure Key Vault (online) or HashiCorp Vault (offline)
    """
    if DEPLOYMENT_MODE == "online":
        logger.debug("Using Azure Key Vault for secrets")
        # TODO: Implement AzureKeyVaultSecretProvider when needed
        raise NotImplementedError(
            "Azure Key Vault provider not yet implemented. "
            "For now, secrets are managed via Azure SDK directly."
        )
    elif DEPLOYMENT_MODE == "offline":
        logger.debug("Using HashiCorp Vault for secrets")
        from providers.local.secrets import LocalSecretProvider
        return LocalSecretProvider()
    else:
        raise ValueError(f"Invalid DEPLOYMENT_MODE: {DEPLOYMENT_MODE}. Must be 'online' or 'offline'")


# Convenience exports
__all__ = [
    "get_message_bus",
    "get_event_publisher",
    "get_credential_provider",
    "get_secret_provider",
]