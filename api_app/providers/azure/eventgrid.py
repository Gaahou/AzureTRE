"""
Azure Event Grid implementation of EventPublisher.

This module provides Azure Event Grid publishing for status changes,
airlock notifications, and other TRE events.
"""

from typing import Optional
from uuid import uuid4
from azure.eventgrid import EventGridEvent
from azure.eventgrid.aio import EventGridPublisherClient
from providers.interfaces import EventPublisher
from providers.azure.credentials import AzureCredentialProvider


class AzureEventGridPublisher(EventPublisher):
    """
    Azure Event Grid event publisher.

    Publishes CloudEvents-formatted events to Azure Event Grid topics.
    """

    def __init__(self):
        """Initialize the Azure Event Grid publisher."""
        self.credential_provider = AzureCredentialProvider()

    async def publish(
        self,
        topic_endpoint: str,
        event_type: str,
        subject: str,
        data: dict,
        event_id: Optional[str] = None,
    ) -> None:
        """
        Publish an event to Azure Event Grid.

        Args:
            topic_endpoint: Event Grid topic endpoint URL
            event_type: Type of event (e.g., "statusChanged", "airlockNotification")
            subject: Event subject (e.g., resource ID)
            data: Event payload data
            event_id: Optional unique event identifier

        Raises:
            Exception: If event publishing fails
        """
        # Generate event ID if not provided
        if event_id is None:
            event_id = str(uuid4())

        # Create Event Grid event
        event = EventGridEvent(
            event_type=event_type,
            subject=subject,
            data=data,
            data_version="1.0",
            id=event_id
        )

        # Publish event using credential provider
        async with self.credential_provider.get_credential_async_context() as credential:
            client = EventGridPublisherClient(topic_endpoint, credential)
            async with client:
                await client.send([event])