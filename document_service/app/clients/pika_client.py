"""
Client for RabbitMQ messages
"""

import json
import logging
import os
from typing import Callable

from aio_pika import ExchangeType, connect_robust

logger = logging.getLogger()


class PikaClient:
    def __init__(self, process_callable: Callable):
        self.rabbit_url = os.getenv(
            'RABBIT_URL', 'amqp://guest:guest@rabbitmq:5672/'
        )
        self.exchange_name = os.getenv('RABBIT_EXCHANGE', 'minio-events')
        self.routing_key = os.getenv('RABBIT_ROUTING_KEY', 'document_tasks')
        self.queue_name = os.getenv('RABBIT_QUEUE', 'document_tasks')
        self.process_callable = process_callable

    async def consume(self):
        try:
            logger.info(
                f'Attempting to connect to RabbitMQ at {self.rabbit_url}'
            )
            connection = await connect_robust(self.rabbit_url)
            logger.info('Connected to RabbitMQ successfully')

            channel = await connection.channel()

            exchange = await channel.declare_exchange(
                self.exchange_name, ExchangeType.DIRECT, durable=True
            )
            logger.info(f'Declared exchange: {self.exchange_name}')

            queue = await channel.declare_queue(self.queue_name, durable=True)
            await queue.bind(exchange, routing_key=self.routing_key)
            logger.info(
                f'Queue {self.queue_name} bound to exchange with routing key {self.routing_key}'
            )

            logger.info('Starting to consume messages...')
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            body = json.loads(message.body.decode())
                        except Exception:
                            body = message.body.decode()
                        logger.info(f'Processing message: {body}')
                        await self.process_callable(body)
        except Exception as e:
            logger.error(f'Error in RabbitMQ consumer: {e}')
            raise
