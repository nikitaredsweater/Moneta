"""
Main FastAPI application module with RabbitMQ listener for MinIO events.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from app.api import app_router
from app.clients import PikaClient
from app.handlers.minio import on_minio_message
from fastapi import FastAPI
from moneta_logging import configure_logging
from moneta_logging.middleware import RequestLoggingMiddleware

# RabbitMQ connection settings
RABBIT_URL = os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@rabbitmq:5672/')
EXCHANGE_NAME = 'minio-events'
ROUTING_KEY = 'document_tasks'
QUEUE_NAME = 'document_tasks'


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event for startup and shutdown."""
    # Configure logging HERE, after Uvicorn has started
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info('[SYSTEM] Document service starting')
    logger.info('[SYSTEM] Logging configured successfully')
    
    # Initialize RabbitMQ consumer
    logger.info('[SYSTEM] Initializing RabbitMQ consumer')
    client = PikaClient(on_minio_message)
    logger.info('[SYSTEM] PikaClient created | starting consumer')
    asyncio.create_task(client.consume())
    logger.info('[SYSTEM] RabbitMQ consumer task started')
    
    yield  # Application runs
    
    # Cleanup on shutdown
    logger.info('[SYSTEM] Application shutting down')


app = FastAPI(
    title='Document Service',
    description='Document management and storage service',
    lifespan=lifespan
)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(app_router)