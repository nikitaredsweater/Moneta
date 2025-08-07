"""
Main FastAPI application module.
"""

from app.api import app_router
from fastapi import FastAPI
import asyncio
import os
from aio_pika import connect_robust, IncomingMessage, ExchangeType
from app.workers.tasks import parse_pdf_task, handle_minio_event  # your Celery task

app = FastAPI()


RABBIT_URL = os.getenv(
    "CELERY_BROKER_URL",
    "amqp://guest:guest@rabbitmq:5672//"
)


app.include_router(app_router)

async def rabbit_consumer():
    # 1) connect
    conn = await connect_robust(RABBIT_URL)
    channel = await conn.channel()
    # 2) declare the same exchange/queue
    exchange = await channel.declare_exchange(
        "minio-events", ExchangeType.DIRECT, durable=True
    )
    queue = await channel.declare_queue(
        "document_tasks", durable=True
    )
    await queue.bind(exchange, routing_key="document_tasks")

    # 3) consume
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                body = message.body.decode()
                # parse JSON if you need more fields
                # data = json.loads(body)
                # fire the Celery task
                handle_minio_event.delay(body)
                # ack happens automatically on exit of message.process()


@app.on_event("startup")
async def start_rabbit():
    # schedule the consumer; it runs in background on the event loop
    asyncio.create_task(rabbit_consumer())

@app.get('/')
def read_root():
    return {'message': 'Hello, world!'}
