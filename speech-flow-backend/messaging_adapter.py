"""Messaging adapter to support both Azure Service Bus and RabbitMQ.

This module provides a unified interface for message queue operations that works with:
- Azure Service Bus (using DefaultAzureCredential)
- RabbitMQ (for local development)
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Optional


class MessageBroker(ABC):
    """Abstract base class for message brokers."""

    @abstractmethod
    async def get_queue_sender(self, queue_name: str):
        """Get a sender for a specific queue.

        Args:
            queue_name: Name of the queue

        Returns:
            Queue sender instance
        """
        pass

    @abstractmethod
    async def get_queue_receiver(self, queue_name: str):
        """Get a receiver for a specific queue.

        Args:
            queue_name: Name of the queue

        Returns:
            Queue receiver instance
        """
        pass

    @abstractmethod
    async def close(self):
        """Close the connection."""
        pass


class AzureServiceBusAdapter(MessageBroker):
    """Azure Service Bus implementation using DefaultAzureCredential."""

    def __init__(
        self,
        fully_qualified_namespace: Optional[str] = None,
        use_connection_string: bool = False,
        connection_string: Optional[str] = None,
    ):
        """Initialize Azure Service Bus adapter.

        Args:
            fully_qualified_namespace: Service Bus namespace FQDN
            use_connection_string: Whether to use connection string (for local testing)
            connection_string: Connection string (only for backward compatibility)
        """
        from azure.servicebus.aio import ServiceBusClient

        self.fully_qualified_namespace = fully_qualified_namespace
        self.use_connection_string = use_connection_string

        if use_connection_string and connection_string:
            # Use connection string (for backward compatibility/local testing)
            self._client = ServiceBusClient.from_connection_string(connection_string)
        else:
            # Use DefaultAzureCredential (production)
            from azure.identity.aio import DefaultAzureCredential

            credential = DefaultAzureCredential()
            self._client = ServiceBusClient(fully_qualified_namespace=fully_qualified_namespace, credential=credential)

    async def get_queue_sender(self, queue_name: str):
        """Get a sender for a specific queue."""
        return self._client.get_queue_sender(queue_name=queue_name)

    async def get_queue_receiver(self, queue_name: str):
        """Get a receiver for a specific queue."""
        return self._client.get_queue_receiver(queue_name=queue_name)

    async def close(self):
        """Close the connection."""
        await self._client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class RabbitMQAdapter(MessageBroker):
    """RabbitMQ implementation for local development.

    Note: This implementation uses blocking pika for simplicity in local development.
    For production async use, consider using aio_pika instead.
    """

    def __init__(self, connection_string: str):
        """Initialize RabbitMQ adapter.

        Args:
            connection_string: AMQP connection string (e.g., amqp://user:pass@host:port/)
        """
        self.connection_string = connection_string
        self.connection = None
        self.channel = None
        self._receivers = {}
        self._senders = {}

    async def _ensure_connection(self) -> None:
        """Ensure connection is established."""
        if self.connection is None or self.connection.is_closed:
            import pika

            # Parse RabbitMQ connection string
            params = pika.URLParameters(self.connection_string)
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()

    async def get_queue_sender(self, queue_name: str):
        """Get a sender for a specific queue."""
        await self._ensure_connection()
        # Declare queue
        self.channel.queue_declare(queue=queue_name, durable=True)
        return RabbitMQSender(self.channel, queue_name)

    async def get_queue_receiver(self, queue_name: str):
        """Get a receiver for a specific queue."""
        await self._ensure_connection()
        # Declare queue
        self.channel.queue_declare(queue=queue_name, durable=True)
        return RabbitMQReceiver(self.channel, queue_name)

    async def close(self):
        """Close the connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class RabbitMQSender:
    """RabbitMQ queue sender"""

    def __init__(self, channel, queue_name: str):
        self.channel = channel
        self.queue_name = queue_name
        import pika

        self._pika = pika

    async def send_messages(self, message):
        """Send a message to the queue"""
        # Extract body from message (compatible with ServiceBusMessage interface)
        if hasattr(message, "body"):
            body = message.body
        elif isinstance(message, str):
            body = message
        else:
            body = str(message)

        # Publish message to RabbitMQ
        self.channel.basic_publish(
            exchange="",
            routing_key=self.queue_name,
            body=body,
            properties=self._pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ),
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class RabbitMQReceiver:
    """RabbitMQ queue receiver"""

    def __init__(self, channel, queue_name: str):
        self.channel = channel
        self.queue_name = queue_name
        self._messages = []

    async def receive_messages(self, max_message_count: int = 1, max_wait_time: int = 5):
        """Receive messages from the queue"""
        messages = []
        for _ in range(max_message_count):
            method_frame, header_frame, body = self.channel.basic_get(queue=self.queue_name, auto_ack=False)
            if method_frame:
                messages.append(RabbitMQMessage(body, method_frame.delivery_tag, self.channel))
            else:
                break
        return messages

    async def complete_message(self, message):
        """Acknowledge message"""
        self.channel.basic_ack(delivery_tag=message.delivery_tag)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def __aiter__(self):
        return self

    async def __anext__(self):
        """Iterate over messages"""
        import asyncio

        # This is a simplified implementation
        # In production, you'd want to use async iterators properly
        while True:
            method_frame, header_frame, body = self.channel.basic_get(queue=self.queue_name, auto_ack=False)
            if method_frame:
                return RabbitMQMessage(body, method_frame.delivery_tag, self.channel)
            await asyncio.sleep(1)


class RabbitMQMessage:
    """Wrapper for RabbitMQ message to match ServiceBus interface"""

    def __init__(self, body, delivery_tag, channel):
        self._body = body
        self.delivery_tag = delivery_tag
        self.channel = channel

    def __str__(self):
        """Return message body as string"""
        if isinstance(self._body, bytes):
            return self._body.decode("utf-8")
        return str(self._body)


class ServiceBusMessage:
    """Wrapper for messages to be sent"""

    def __init__(self, body: str, message_id: Optional[str] = None, subject: Optional[str] = None):
        self.body = body
        self.message_id = message_id
        self.subject = subject


def get_message_broker(
    fully_qualified_namespace: Optional[str] = None, connection_string: Optional[str] = None
) -> MessageBroker:
    """Factory function to get the appropriate message broker.

    Args:
        fully_qualified_namespace: Service Bus namespace FQDN (for AZURE mode)
        connection_string: Connection string (for RabbitMQ or legacy Service Bus)

    Returns:
        MessageBroker instance (either Azure Service Bus or RabbitMQ)
    """
    environment = os.getenv("ENVIRONMENT", "AZURE").upper()

    if environment == "LOCAL":
        # Use RabbitMQ for local development
        if connection_string is None:
            connection_string = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        return RabbitMQAdapter(connection_string)
    else:
        # Use Azure Service Bus
        # Check if connection string provided (for backward compatibility)
        if connection_string is None:
            connection_string = os.getenv("SERVICEBUS_CONNECTION_STRING", "")

        # Check if this is a legacy connection string or local testing
        use_connection_string = "SharedAccessKey" in connection_string or "localhost" in connection_string

        if not use_connection_string:
            # Production: Use DefaultAzureCredential
            if fully_qualified_namespace is None:
                fully_qualified_namespace = os.getenv("SERVICEBUS_FQDN", "")
            return AzureServiceBusAdapter(
                fully_qualified_namespace=fully_qualified_namespace, use_connection_string=False
            )
        else:
            # Legacy/Testing: Use connection string
            return AzureServiceBusAdapter(use_connection_string=True, connection_string=connection_string)
