"""
Creates a client for minIO service.
"""

import logging
import os

from minio import Minio

logger = logging.getLogger(__name__)

_endpoint = os.getenv('MINIO_ENDPOINT', 'minio:9000')

minio_client = Minio(
    endpoint=_endpoint,
    access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
    secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
    secure=False,
)

logger.info('[EXTERNAL] MinIO client initialized | endpoint=%s', _endpoint)
