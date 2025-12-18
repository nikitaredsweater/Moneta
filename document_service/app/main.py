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
from moneta_logging import configure_logging
from moneta_logging.middleware import RequestLoggingMiddleware

# Configure logging from environment variables (LOG_LEVEL, LOG_OUTPUT, LOG_FILE_PATH)
configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(title='Document Service', description='Document management and storage service')
app.add_middleware(RequestLoggingMiddleware)
app.include_router(app_router)

logger.info('[SYSTEM] Document service starting')

# RabbitMQ connection settings
RABBIT_URL = os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@rabbitmq:5672/')
EXCHANGE_NAME = 'minio-events'
ROUTING_KEY = 'document_tasks'
QUEUE_NAME = 'document_tasks'


@app.on_event('startup')
async def startup_event():
    """Initialize RabbitMQ consumer on application startup."""
    logger.info('[SYSTEM] FastAPI startup event triggered')
    client = PikaClient(on_minio_message)
    logger.info('[SYSTEM] PikaClient created | starting consumer')
    asyncio.create_task(client.consume())
    logger.info('[SYSTEM] RabbitMQ consumer task started')
