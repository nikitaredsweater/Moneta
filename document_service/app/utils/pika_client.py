"""
Client for RabbitMQ messages
"""
import os
import json
from aio_pika import connect_robust, ExchangeType
from typing import Callable

class PikaClient:
    def __init__(self, process_callable: Callable):
        self.rabbit_url = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")
        self.exchange_name = os.getenv("RABBIT_EXCHANGE", "minio-events")
        self.routing_key = os.getenv("RABBIT_ROUTING_KEY", "document_tasks")
        self.queue_name = os.getenv("RABBIT_QUEUE", "document_tasks")
        self.process_callable = process_callable

    async def consume(self):
        connection = await connect_robust(self.rabbit_url)
        channel = await connection.channel()

        exchange = await channel.declare_exchange(
            self.exchange_name, ExchangeType.DIRECT, durable=True
        )

        queue = await channel.declare_queue(self.queue_name, durable=True)
        await queue.bind(exchange, routing_key=self.routing_key)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        body = json.loads(message.body.decode())
                    except Exception:
                        body = message.body.decode()
                    await self.process_callable(body)