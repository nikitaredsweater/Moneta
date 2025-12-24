"""
Main FastAPI application module with RabbitMQ listener for MinIO events.

This service uses JWT authentication via moneta-auth package.
Only the public key is required for token verification (no token creation).
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
from moneta_auth import jwt_keys, JWTAuthMiddleware
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
    # Configure logging AFTER Uvicorn has initialized
    # This prevents Uvicorn from overriding our configuration
    configure_logging()

    logger = logging.getLogger(__name__)
    logger.info('[SYSTEM] Document service starting')
    logger.info('[SYSTEM] Logging configured successfully')

    # Load JWT public key for token verification
    # This service only verifies tokens, it does not create them
    try:
        jwt_keys.load_public_key()
        logger.info('[SYSTEM] JWT public key loaded successfully')
    except Exception as e:
        logger.error(
            '[SYSTEM] FATAL: JWT public key failed to load. '
            'Ensure JWT_PUBLIC_KEY_PATH environment variable is set '
            'and points to a valid PEM public key file. Error: %s', e
        )
        raise RuntimeError(f'JWT public key required but failed to load: {e}') from e
    
    # Check that log file was created
    log_file_path = os.getenv('LOG_FILE_PATH', 'logs/app.log')
    logger.info(f'[SYSTEM] Logging to file: {log_file_path}')
    
    # Initialize RabbitMQ consumer
    logger.info('[SYSTEM] Initializing RabbitMQ consumer')
    client = PikaClient(on_minio_message)
    logger.info('[SYSTEM] PikaClient created | starting consumer')
    asyncio.create_task(client.consume())
    logger.info('[SYSTEM] RabbitMQ consumer task started')
    
    yield  # Application runs here
    
    # Cleanup on shutdown
    logger.info('[SYSTEM] Application shutting down')


app = FastAPI(
    title='Document Service',
    description='Document management and storage service',
    lifespan=lifespan  # This ensures logging is configured at the right time
)

# Middleware order matters: they execute in reverse order of addition
# 1. RequestLoggingMiddleware (added last, executes first)
# 2. JWTAuthMiddleware (added second, executes second)
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(app_router)