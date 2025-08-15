"""
Main FastAPI application module with RabbitMQ listener for MinIO events.
"""

import asyncio
import logging
import os

import app.gen.document_ingest_pb2 as pb
from app.api import app_router
from app.clients import MonolithGrpcClient, PikaClient
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


async def handle_minio_event(event):
    # Your document processing logic here
    # TODO: Only for test we do not see what type of event this is
    logger.info('📦 Received event: %s', event)

    async with MonolithGrpcClient(
        # target='monolith.internal:50061',
        metadata=[('authorization', 'Bearer <token>')],
        timeout_sec=3.0,
    ) as client:

        resp = await client.save_document(
            company_id='2a2f45f7-0b21-4b36-b0ad-0b2d1c2ad111',
            user_id='d4a50a3f-98f0-45a9-8b20-8b6d3d7a1f22',
            document_type=pb.USER_DOCUMENT,  # or pb.COMPANY_DOCUMENT, etc.
        )
        # Handle CREATED / ALREADY_EXISTS as your app's success states:
        logger.info(
            f'Received gRPC respone: {resp.status}, {resp.row_id}, {resp.message}'
        )


@app.on_event('startup')
async def startup_event():
    logger.info('FastAPI startup event triggered')
    client = PikaClient(handle_minio_event)
    logger.info('Created PikaClient, starting consumer...')
    asyncio.create_task(client.consume())


@app.get('/')
def read_root():
    return {'message': 'Hello, world!'}
