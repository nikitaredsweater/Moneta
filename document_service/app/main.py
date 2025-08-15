"""
Main FastAPI application module with RabbitMQ listener for MinIO events.
"""

import os
import asyncio
from fastapi import FastAPI
from app.api import app_router
from app.utils.pika_client import PikaClient

app = FastAPI()
app.include_router(app_router)

# RabbitMQ connection settings
RABBIT_URL = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE_NAME = "minio-events"
ROUTING_KEY = "document_tasks"
QUEUE_NAME = "document_tasks"

async def handle_minio_event(event):
    # Your document processing logic here
    print("📦 Received event:", event)

@app.on_event("startup")
async def startup_event():
    client = PikaClient(handle_minio_event)
    asyncio.create_task(client.consume())


@app.get("/")
def read_root():
    return {"message": "Hello, world!"}
