"""
Client for RabbitMQ messages.

Provides an async consumer for RabbitMQ queues, typically used to receive
MinIO event notifications.
"""

import json
import logging
import os
from typing import Callable

from aio_pika import ExchangeType, connect_robust

logger = logging.getLogger(__name__)


class PikaClient:
    """
    Async RabbitMQ client for consuming messages from a queue.

    Connects to RabbitMQ, declares an exchange and queue, and processes
    messages using the provided callback function.
    """

    def __init__(self, process_callable: Callable):
        """
        Initialize the PikaClient.

        Args:
            process_callable: Async function to process each message.
        """
        self.rabbit_url = os.getenv(
            'RABBIT_URL', 'amqp://guest:guest@rabbitmq:5672/'
        )
        self.exchange_name = os.getenv('RABBIT_EXCHANGE', 'minio-events')
        self.routing_key = os.getenv('RABBIT_ROUTING_KEY', 'document_tasks')
        self.queue_name = os.getenv('RABBIT_QUEUE', 'document_tasks')
        self.process_callable = process_callable
        logger.debug(
            '[EXTERNAL] PikaClient initialized | exchange=%s | queue=%s | routing_key=%s',
            self.exchange_name,
            self.queue_name,
            self.routing_key,
        )

    async def consume(self):
        """
        Connect to RabbitMQ and start consuming messages.

        This method runs indefinitely, processing messages as they arrive.
        """
        try:
            logger.info('[EXTERNAL] Connecting to RabbitMQ | url=%s', self.rabbit_url.split('@')[-1])
            connection = await connect_robust(self.rabbit_url)
            logger.info('[EXTERNAL] RabbitMQ connected successfully')

            channel = await connection.channel()
            logger.debug('[EXTERNAL] RabbitMQ channel opened')

            exchange = await channel.declare_exchange(
                self.exchange_name, ExchangeType.DIRECT, durable=True
            )
            logger.info('[EXTERNAL] RabbitMQ exchange declared | exchange=%s', self.exchange_name)

            queue = await channel.declare_queue(self.queue_name, durable=True)
            await queue.bind(exchange, routing_key=self.routing_key)
            logger.info(
                '[EXTERNAL] RabbitMQ queue bound | queue=%s | exchange=%s | routing_key=%s',
                self.queue_name,
                self.exchange_name,
                self.routing_key,
            )

            logger.info('[EXTERNAL] RabbitMQ consumer started | queue=%s', self.queue_name)
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            body = json.loads(message.body.decode())
                        except json.JSONDecodeError:
                            body = message.body.decode()
                            logger.warning(
                                '[EXTERNAL] RabbitMQ message not valid JSON | raw_body_length=%d',
                                len(str(body)),
                            )

                        logger.debug(
                            '[EXTERNAL] RabbitMQ message received | message_id=%s | routing_key=%s',
                            message.message_id or 'none',
                            message.routing_key or 'none',
                        )

                        try:
                            await self.process_callable(body)
                            logger.info(
                                '[EXTERNAL] RabbitMQ message processed | message_id=%s',
                                message.message_id or 'none',
                            )
                        except Exception as e:
                            logger.error(
                                '[EXTERNAL] RabbitMQ message processing failed | message_id=%s | error_type=%s | error=%s',
                                message.message_id or 'none',
                                type(e).__name__,
                                str(e),
                            )
                            raise

        except Exception as e:
            logger.error(
                '[EXTERNAL] RabbitMQ consumer error | error_type=%s | error=%s',
                type(e).__name__,
                str(e),
            )
            raise
