import os
from celery import Celery
from kombu import Exchange, Queue

# Broker URL
CELERY_BROKER_URL = os.getenv(
    'CELERY_BROKER_URL',
    'amqp://guest:guest@rabbitmq:5672//'
)

celery_app = Celery(
    'document_tasks',
    broker=CELERY_BROKER_URL,
    backend=None,
    include=['app.workers.tasks'],
)

# 1) Define your queue bound to minio-events
celery_app.conf.task_queues = (
    Queue(
        'document_tasks',
        exchange=Exchange('minio-events', type='direct'),
        routing_key='document_tasks',
    ),
)

# 2) Make that your DEFAULT queue/exchange/routing key
celery_app.conf.task_default_queue = 'document_tasks'
celery_app.conf.task_default_exchange = 'minio-events'
celery_app.conf.task_default_exchange_type = 'direct'
celery_app.conf.task_default_routing_key = 'document_tasks'

# (Optional) you can keep or remove task_routes now
celery_app.conf.task_routes = {
    'app.workers.tasks.*': {'queue': 'document_tasks'}
}
