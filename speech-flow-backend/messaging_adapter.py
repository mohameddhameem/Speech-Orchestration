"""
Messaging adapter to support both Azure Service Bus and RabbitMQ
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Optional, Any


class MessageBroker(ABC):
    """Abstract base class for message brokers"""
    
    @abstractmethod
    async def get_queue_sender(self, queue_name: str):
        """Get a sender for a specific queue"""
        pass
    
    @abstractmethod
    async def get_queue_receiver(self, queue_name: str):
        """Get a receiver for a specific queue"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close the connection"""
        pass


class AzureServiceBusAdapter(MessageBroker):
    """Azure Service Bus implementation"""
    
    def __init__(self, connection_string: str):
        from azure.servicebus.aio import ServiceBusClient
        self.connection_string = connection_string
        self._client = ServiceBusClient.from_connection_string(connection_string)
    
    async def get_queue_sender(self, queue_name: str):
        return self._client.get_queue_sender(queue_name=queue_name)
    
    async def get_queue_receiver(self, queue_name: str):
        return self._client.get_queue_receiver(queue_name=queue_name)
    
    async def close(self):
        await self._client.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class RabbitMQAdapter(MessageBroker):
    """RabbitMQ implementation for local development"""
    
    def __init__(self, connection_string: str):
        import pika
        from pika.adapters.asyncio_connection import AsyncioConnection
        
        # Parse connection string (format: amqp://user:pass@host:port/vhost)
        self.connection_string = connection_string
        self.connection = None
        self.channel = None
        self._pika = pika
        self._receivers = {}
        self._senders = {}
    
    async def _ensure_connection(self):
        """Ensure connection is established"""
        if self.connection is None or self.connection.is_closed:
            import pika
            # Parse RabbitMQ connection string
            params = pika.URLParameters(self.connection_string)
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
    
    async def get_queue_sender(self, queue_name: str):
        """Get a sender for a specific queue"""
        await self._ensure_connection()
        # Declare queue
        self.channel.queue_declare(queue=queue_name, durable=True)
        return RabbitMQSender(self.channel, queue_name)
    
    async def get_queue_receiver(self, queue_name: str):
        """Get a receiver for a specific queue"""
        await self._ensure_connection()
        # Declare queue
        self.channel.queue_declare(queue=queue_name, durable=True)
        return RabbitMQReceiver(self.channel, queue_name)
    
    async def close(self):
        """Close the connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
    
    async def __aenter__(self):
        await self._ensure_connection()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
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
        if hasattr(message, 'body'):
            body = message.body
        elif isinstance(message, str):
            body = message
        else:
            body = str(message)
        
        # Publish message to RabbitMQ
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queue_name,
            body=body,
            properties=self._pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
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
            method_frame, header_frame, body = self.channel.basic_get(
                queue=self.queue_name,
                auto_ack=False
            )
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
            method_frame, header_frame, body = self.channel.basic_get(
                queue=self.queue_name,
                auto_ack=False
            )
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
            return self._body.decode('utf-8')
        return str(self._body)


class ServiceBusMessage:
    """Wrapper for messages to be sent"""
    
    def __init__(self, body: str, message_id: Optional[str] = None, subject: Optional[str] = None):
        self.body = body
        self.message_id = message_id
        self.subject = subject


def get_message_broker(connection_string: Optional[str] = None) -> MessageBroker:
    """
    Factory function to get the appropriate message broker based on environment.
    
    Args:
        connection_string: Connection string for the message broker.
                          If None, uses SERVICEBUS_CONNECTION_STRING or RABBITMQ_URL env var.
    
    Returns:
        MessageBroker instance (either Azure Service Bus or RabbitMQ)
    """
    environment = os.getenv("ENVIRONMENT", "AZURE").upper()
    
    if environment == "LOCAL":
        # Use RabbitMQ for local development
        if connection_string is None:
            connection_string = os.getenv(
                "RABBITMQ_URL", 
                "amqp://guest:guest@localhost:5672/"
            )
        return RabbitMQAdapter(connection_string)
    else:
        # Use Azure Service Bus
        if connection_string is None:
            connection_string = os.getenv("SERVICEBUS_CONNECTION_STRING", "")
        return AzureServiceBusAdapter(connection_string)
