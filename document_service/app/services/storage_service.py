"""
module for synchronous actions performed on storage
"""

from datetime import timedelta

from app.utils import minio_client


def generate_presigned_upload_url(key: str) -> str:
    """
    Returns a URL which should be used to upload files to bucket
    """
    url = minio_client.presigned_put_object(
        bucket_name='documents',  # TODO: <--- This hardcoded value is not ideal
        object_name=key,
        expires=timedelta(minutes=10),
    )
    return url
