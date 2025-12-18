"""
Module for synchronous actions performed on storage.

Provides functions for generating presigned URLs for MinIO operations.
"""

import logging
from datetime import timedelta

from app.clients import minio_client

logger = logging.getLogger(__name__)


def generate_presigned_url(
    key: str, operation: str = 'upload', expires_minutes: int = 10
) -> str:
    """
    Returns a presigned URL for MinIO operations.

    Arguments:
        key (str) - name of the file as it will appear in the bucket
        operation (str) - operation type: 'upload' or 'download'
        expires_minutes (int) - URL expiration time in minutes

    Returns:
        str - full presigned URL for the specified operation
    """
    bucket_name = 'documents'  # TODO: <--- This hardcoded value is not ideal
    expires = timedelta(minutes=expires_minutes)

    logger.debug(
        '[EXTERNAL] Generating presigned URL | operation=%s | bucket=%s | key=%s | expires_min=%d',
        operation,
        bucket_name,
        key,
        expires_minutes,
    )

    if operation == 'upload':
        url = minio_client.presigned_put_object(
            bucket_name=bucket_name,
            object_name=key,
            expires=expires,
        )
    elif operation == 'download':
        url = minio_client.presigned_get_object(
            bucket_name=bucket_name,
            object_name=key,
            expires=expires,
        )
    else:
        logger.error('[EXTERNAL] Unsupported MinIO operation | operation=%s', operation)
        raise ValueError(
            f"Unsupported operation: {operation}. Use 'upload' or 'download'"
        )

    logger.info(
        '[EXTERNAL] Presigned URL generated | operation=%s | bucket=%s | key=%s',
        operation,
        bucket_name,
        key,
    )

    return url


def generate_presigned_upload_url(key: str) -> str:
    """
    Returns a URL which should be used to upload files to bucket.

    This is a convenience wrapper around generate_presigned_url for backward compatibility.

    Arguments:
        key (str) - name of the file as it will appear in the bucket

    Returns:
        str - full URL that a client can use to load the file into the system
    """
    return generate_presigned_url(key, operation='upload')


def generate_presigned_download_url(key: str) -> str:
    """
    Returns a URL which should be used to download files from bucket.

    Arguments:
        key (str) - name of the file in the bucket

    Returns:
        str - full URL that a client can use to download the file
    """
    return generate_presigned_url(key, operation='download')
