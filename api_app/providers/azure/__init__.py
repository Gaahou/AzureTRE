"""
Azure provider implementations.

This package contains Azure-specific implementations of the provider interfaces
for online (Azure cloud) deployment mode.

Implementations:
- AzureCredentialProvider: Azure AD / Managed Identity authentication
- AzureServiceBusMessageBus: Azure Service Bus messaging
- AzureEventGridPublisher: Azure Event Grid event publishing

Usage:
    from providers.azure.credentials import AzureCredentialProvider
    from providers.azure.servicebus import AzureServiceBusMessageBus
    from providers.azure.eventgrid import AzureEventGridPublisher

    # Or use the factory (recommended)
    from providers.factory import get_credential_provider, get_message_bus, get_event_publisher
"""

from providers.azure.credentials import AzureCredentialProvider
from providers.azure.servicebus import AzureServiceBusMessageBus
from providers.azure.eventgrid import AzureEventGridPublisher

__all__ = [
    "AzureCredentialProvider",
    "AzureServiceBusMessageBus",
    "AzureEventGridPublisher",
]