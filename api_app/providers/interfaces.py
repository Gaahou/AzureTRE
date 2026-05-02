"""
Abstract base classes for provider interfaces.

These interfaces define the contract that all provider implementations must follow,
enabling seamless switching between online (Azure) and offline (local) deployment modes.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional
from contextlib import asynccontextmanager
from azure.core.credentials import TokenCredential


class MessageBus(ABC):
    """
    Abstract interface for message queue operations.

    Implementations:
    - Azure Service Bus (online mode)
    - RabbitMQ (offline mode)
    """

    @abstractmethod
    async def send_message(
        self,
        queue_name: str,
        message_body: str,
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Send a message to the specified queue.

        Args:
            queue_name: Name of the queue to send to
            message_body: Message content (JSON string or plain text)
            correlation_id: Optional correlation ID for tracking
            session_id: Optional session ID for session-enabled queues

        Raises:
            Exception: If message sending fails
        """
        pass

    @abstractmethod
    async def receive_messages(
        self,
        queue_name: str,
        callback: Callable[[Any], None],
        max_messages: int = 1,
    ) -> None:
        """
        Receive messages from the specified queue and process with callback.

        Args:
            queue_name: Name of the queue to receive from
            callback: Async function to process each message
            max_messages: Maximum number of messages to receive

        Raises:
            Exception: If message receiving fails
        """
        pass


class EventPublisher(ABC):
    """
    Abstract interface for event publishing operations.

    Implementations:
    - Azure Event Grid (online mode)
    - RabbitMQ Topic Exchange (offline mode)
    """

    @abstractmethod
    async def publish(
        self,
        topic_endpoint: str,
        event_type: str,
        subject: str,
        data: dict,
        event_id: Optional[str] = None,
    ) -> None:
        """
        Publish an event to the specified topic.

        Args:
            topic_endpoint: Topic endpoint URL or name
            event_type: Type of event (e.g., "statusChanged", "airlockNotification")
            subject: Event subject (e.g., resource ID)
            data: Event payload data
            event_id: Optional unique event identifier

        Raises:
            Exception: If event publishing fails
        """
        pass


class CredentialProvider(ABC):
    """
    Abstract interface for credential and authentication operations.

    Implementations:
    - Azure AD / Managed Identity (online mode)
    - Keycloak OIDC (offline mode)
    """

    @abstractmethod
    def get_credential(self) -> TokenCredential:
        """
        Get a credential object for synchronous operations.

        Returns:
            TokenCredential: Credential object compatible with Azure SDKs

        Raises:
            Exception: If credential acquisition fails
        """
        pass

    @abstractmethod
    async def get_credential_async(self) -> TokenCredential:
        """
        Get a credential object for asynchronous operations.

        Returns:
            TokenCredential: Async credential object compatible with Azure SDKs

        Raises:
            Exception: If credential acquisition fails
        """
        pass

    @abstractmethod
    @asynccontextmanager
    async def get_credential_async_context(self) -> TokenCredential:
        """
        Get a credential object as an async context manager.

        Yields:
            TokenCredential: Async credential object that is properly cleaned up

        Raises:
            Exception: If credential acquisition fails
        """
        pass

    @abstractmethod
    async def get_token(self, scopes: list[str]) -> str:
        """
        Get an access token for the specified scopes.

        Args:
            scopes: List of OAuth2 scopes to request

        Returns:
            str: Access token

        Raises:
            Exception: If token acquisition fails
        """
        pass