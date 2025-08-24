"""
Main FastAPI application module with RabbitMQ listener for MinIO events.
"""

import asyncio
import logging
import os


from app.api import app_router
from app.clients import MonolithGrpcClient, PikaClient
from fastapi import FastAPI

from app.utils.minio_event_parsing import MinIOEvent, parse_minio_event
from app.services import handle_new_document_creation

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


async def handle_minio_event(event):
    """
    Handler for general event. For now we assume that all
    events are minio events.
    """
    logger.info('📦 Received NEW event: %s', event)
    minio_event = parse_minio_event(event)
    logger.info('📦 Received event: %s', minio_event)
    
    # Handle the new document being created
    if minio_event.event_name == 's3:ObjectCreated:Put':
        await handle_new_document_creation(minio_event)


@app.on_event('startup')
async def startup_event():
    logger.info('FastAPI startup event triggered')
    client = PikaClient(handle_minio_event)
    logger.info('Created PikaClient, starting consumer...')
    asyncio.create_task(client.consume())


@app.get('/')
def read_root():
    return {'message': 'Hello, world!'}
