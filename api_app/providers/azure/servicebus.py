"""
Azure Service Bus implementation of MessageBus.

This module provides Azure Service Bus messaging for resource deployment
requests and status updates.
"""

from typing import Any, Callable, Optional
from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient
from core.config import SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE
from providers.interfaces import MessageBus
from providers.azure.credentials import AzureCredentialProvider
from services.logging import logger


class AzureServiceBusMessageBus(MessageBus):
    """
    Azure Service Bus message bus implementation.

    Provides queue-based messaging using Azure Service Bus for
    deployment requests and status updates.
    """

    def __init__(self):
        """Initialize the Azure Service Bus message bus."""
        self.credential_provider = AzureCredentialProvider()
        self.namespace = SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE

    async def send_message(
        self,
        queue_name: str,
        message_body: str,
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Send a message to an Azure Service Bus queue.

        Args:
            queue_name: Name of the Service Bus queue
            message_body: Message content (JSON string or plain text)
            correlation_id: Optional correlation ID for tracking
            session_id: Optional session ID for session-enabled queues

        Raises:
            Exception: If message sending fails
        """
        # Create Service Bus message
        message = ServiceBusMessage(
            body=message_body,
            correlation_id=correlation_id,
            session_id=session_id
        )

        logger.info(
            f"Sending message to queue '{queue_name}' "
            f"(correlation_id: {correlation_id}, session_id: {session_id})"
        )

        # Send message using credential provider
        async with self.credential_provider.get_credential_async_context() as credential:
            service_bus_client = ServiceBusClient(self.namespace, credential)

            async with service_bus_client:
                sender = service_bus_client.get_queue_sender(queue_name=queue_name)

                async with sender:
                    await sender.send_messages(message)

        logger.info(f"Message sent successfully to queue '{queue_name}'")

    async def receive_messages(
        self,
        queue_name: str,
        callback: Callable[[Any], None],
        max_messages: int = 1,
    ) -> None:
        """
        Receive messages from an Azure Service Bus queue.

        Args:
            queue_name: Name of the Service Bus queue
            callback: Async function to process each message
            max_messages: Maximum number of messages to receive

        Raises:
            Exception: If message receiving fails
        """
        logger.info(f"Receiving messages from queue '{queue_name}' (max: {max_messages})")

        async with self.credential_provider.get_credential_async_context() as credential:
            service_bus_client = ServiceBusClient(self.namespace, credential)

            async with service_bus_client:
                receiver = service_bus_client.get_queue_receiver(queue_name=queue_name)

                async with receiver:
                    messages = await receiver.receive_messages(
                        max_message_count=max_messages,
                        max_wait_time=5
                    )

                    for message in messages:
                        try:
                            # Process message with callback
                            await callback(message)
                            # Complete the message (remove from queue)
                            await receiver.complete_message(message)
                            logger.info(f"Message processed and completed: {message.message_id}")
                        except Exception as e:
                            logger.error(f"Error processing message {message.message_id}: {e}")
                            # Abandon the message (return to queue for retry)
                            await receiver.abandon_message(message)
                            raise