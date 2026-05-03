"""
RabbitMQ implementation of MessageBus.

This module provides RabbitMQ messaging for resource deployment
requests and status updates in offline mode.
"""

import json
from typing import Any, Callable, Optional
from aio_pika import connect_robust, Message, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractChannel
from core.config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_VHOST,
)
from providers.interfaces import MessageBus
from services.logging import logger


class RabbitMQMessageBus(MessageBus):
    """
    RabbitMQ message bus implementation.

    Provides queue-based messaging using RabbitMQ for
    deployment requests and status updates in offline mode.

    Queue name mapping (Azure Service Bus → RabbitMQ):
    - workspacequeue → workspacequeue
    - deploymentstatus → deploymentstatus
    """

    def __init__(self):
        """Initialize the RabbitMQ message bus."""
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.connection_url = (
            f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@"
            f"{RABBITMQ_HOST}:{RABBITMQ_PORT}{RABBITMQ_VHOST}"
        )

    async def _ensure_connection(self) -> AbstractChannel:
        """
        Ensure RabbitMQ connection and channel are established.

        Returns:
            AbstractChannel: Active RabbitMQ channel

        Raises:
            Exception: If connection fails
        """
        if self.connection is None or self.connection.is_closed:
            logger.info(f"Connecting to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
            self.connection = await connect_robust(self.connection_url)
            logger.info("RabbitMQ connection established")

        if self.channel is None or self.channel.is_closed:
            self.channel = await self.connection.channel()
            logger.info("RabbitMQ channel opened")

        return self.channel

    async def send_message(
        self,
        queue_name: str,
        message_body: str,
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Send a message to a RabbitMQ queue.

        Args:
            queue_name: Name of the RabbitMQ queue
            message_body: Message content (JSON string or plain text)
            correlation_id: Optional correlation ID for tracking
            session_id: Optional session ID (stored in headers)

        Raises:
            Exception: If message sending fails
        """
        channel = await self._ensure_connection()

        # Declare queue (idempotent - creates if doesn't exist)
        queue = await channel.declare_queue(queue_name, durable=True)

        # Build message headers
        headers = {}
        if session_id:
            headers["session_id"] = session_id

        # Create RabbitMQ message
        message = Message(
            body=message_body.encode(),
            correlation_id=correlation_id,
            headers=headers if headers else None,
            delivery_mode=2,  # Persistent message
        )

        logger.info(
            f"Sending message to queue '{queue_name}' "
            f"(correlation_id: {correlation_id}, session_id: {session_id})"
        )

        # Publish to queue
        await channel.default_exchange.publish(
            message,
            routing_key=queue_name,
        )

        logger.info(f"Message sent successfully to queue '{queue_name}'")

    async def receive_messages(
        self,
        queue_name: str,
        callback: Callable[[Any], None],
        max_messages: int = 1,
    ) -> None:
        """
        Receive messages from a RabbitMQ queue.

        Args:
            queue_name: Name of the RabbitMQ queue
            callback: Async function to process each message
            max_messages: Maximum number of messages to receive

        Raises:
            Exception: If message receiving fails
        """
        channel = await self._ensure_connection()

        # Declare queue
        queue = await channel.declare_queue(queue_name, durable=True)

        logger.info(f"Receiving messages from queue '{queue_name}' (max: {max_messages})")

        # Set prefetch count
        await channel.set_qos(prefetch_count=max_messages)

        # Process messages
        message_count = 0
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                if message_count >= max_messages:
                    break

                async with message.process():
                    try:
                        # Create a message object compatible with callback expectations
                        message_data = {
                            "message_id": message.message_id,
                            "body": message.body.decode(),
                            "correlation_id": message.correlation_id,
                            "headers": message.headers or {},
                        }

                        # Process message with callback
                        await callback(message_data)

                        logger.info(
                            f"Message processed and acknowledged: {message.message_id}"
                        )
                        message_count += 1

                    except Exception as e:
                        logger.error(
                            f"Error processing message {message.message_id}: {e}"
                        )
                        # Message will be rejected (nacked) and requeued
                        raise

    async def close(self) -> None:
        """Close RabbitMQ connection gracefully."""
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
            logger.info("RabbitMQ channel closed")

        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")