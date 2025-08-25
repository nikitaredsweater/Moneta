"""
Main FastAPI application module with RabbitMQ listener for MinIO events.
"""

import asyncio
import logging
import os

from app.api import app_router
from app.clients import PikaClient
from app.handlers.minio import on_minio_message
from fastapi import FastAPI

app = FastAPI()
app.include_router(app_router)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)
logger.info('Starting application')


# RabbitMQ connection settings
RABBIT_URL = os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@rabbitmq:5672/')
EXCHANGE_NAME = 'minio-events'
ROUTING_KEY = 'document_tasks'
QUEUE_NAME = 'document_tasks'


@app.on_event('startup')
async def startup_event():
    logger.info('FastAPI startup event triggered')
    client = PikaClient(on_minio_message)  # New handler
    logger.info('Created PikaClient, starting consumer...')
    asyncio.create_task(client.consume())
