# worker/tasks.py

from app.database.mongo import insert_document
from app.workers.celery_app import celery_app
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@celery_app.task
def parse_pdf_task(file_key: str):
    print(f'📄 Parsing PDF: {file_key}')
    logger.info(f'📄 Parsing PDF: {file_key}')

    # Simulate parsing logic
    parsed_data = {
        'object_key': file_key,
        'instrument_id': 'abc123',
        'status': 'parsed',
        'parsed': {'text': 'This is a fake parse result.', 'pages': 5},
    }

    insert_document(parsed_data)

    # Here you'd add logic to fetch from MinIO, parse, store metadata, etc.
    return f'Parsed {file_key}'
