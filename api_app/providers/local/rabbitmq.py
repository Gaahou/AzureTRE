"""
RabbitMQ implementation of MessageBus and EventPublisher.

This module provides RabbitMQ messaging for resource deployment
requests, status updates, and event publishing in offline mode.
"""

import json
from typing import Any, Callable, Optional
from uuid import uuid4
from datetime import datetime, timezone
from aio_pika import connect_robust, Message, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractChannel
from core.config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_VHOST,
)
from providers.interfaces import MessageBus, EventPublisher
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


class RabbitMQEventPublisher(EventPublisher):
    """
    RabbitMQ event publisher implementation.

    Publishes CloudEvents-formatted events to RabbitMQ topic exchanges,
    replicating Azure Event Grid functionality in offline mode.

    Topic endpoint mapping (Azure Event Grid → RabbitMQ):
    - statusChanged topic → tre.events.status exchange
    - airlockNotification topic → tre.events.airlock exchange
    """

    def __init__(self):
        """Initialize the RabbitMQ event publisher."""
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

    def _extract_exchange_name(self, topic_endpoint: str) -> str:
        """
        Extract exchange name from topic endpoint URL.

        Maps Azure Event Grid topic endpoints to RabbitMQ exchange names.

        Args:
            topic_endpoint: Azure Event Grid topic endpoint URL

        Returns:
            str: RabbitMQ exchange name
        """
        # Extract topic type from URL
        # Example: https://.../topics/statusChanged → tre.events.status
        if "statusChanged" in topic_endpoint or "status" in topic_endpoint.lower():
            return "tre.events.status"
        elif "airlock" in topic_endpoint.lower():
            return "tre.events.airlock"
        else:
            # Default exchange for other event types
            return "tre.events.general"

    async def publish(
        self,
        topic_endpoint: str,
        event_type: str,
        subject: str,
        data: dict,
        event_id: Optional[str] = None,
    ) -> None:
        """
        Publish an event to RabbitMQ topic exchange.

        Args:
            topic_endpoint: Topic endpoint URL (used to determine exchange)
            event_type: Type of event (e.g., "statusChanged", "airlockNotification")
            subject: Event subject (e.g., resource ID)
            data: Event payload data
            event_id: Optional unique event identifier

        Raises:
            Exception: If event publishing fails
        """
        channel = await self._ensure_connection()

        # Generate event ID if not provided
        if event_id is None:
            event_id = str(uuid4())

        # Extract exchange name from topic endpoint
        exchange_name = self._extract_exchange_name(topic_endpoint)

        # Declare topic exchange (idempotent)
        exchange = await channel.declare_exchange(
            exchange_name,
            ExchangeType.TOPIC,
            durable=True
        )

        # Create CloudEvents-formatted event
        cloud_event = {
            "specversion": "1.0",
            "id": event_id,
            "type": event_type,
            "source": "azure-tre-api",
            "subject": subject,
            "time": datetime.now(timezone.utc).isoformat(),
            "datacontenttype": "application/json",
            "data": data,
            "dataversion": "1.0"
        }

        # Create RabbitMQ message
        message = Message(
            body=json.dumps(cloud_event).encode(),
            content_type="application/cloudevents+json",
            message_id=event_id,
            delivery_mode=2,  # Persistent message
        )

        # Use event_type as routing key for topic exchange
        routing_key = event_type

        logger.info(
            f"Publishing event to exchange '{exchange_name}' "
            f"(type: {event_type}, subject: {subject}, id: {event_id})"
        )

        # Publish to topic exchange
        await exchange.publish(message, routing_key=routing_key)

        logger.info(
            f"Event published successfully to exchange '{exchange_name}' "
            f"with routing key '{routing_key}'"
        )

    async def close(self) -> None:
        """Close RabbitMQ connection gracefully."""
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
            logger.info("RabbitMQ channel closed")

        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")