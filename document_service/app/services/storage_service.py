"""
module for synchronous actions performed on storage
"""

from datetime import timedelta

from app.clients import minio_client


def generate_presigned_upload_url(key: str) -> str:
    """
    Returns a URL which should be used to upload files to bucket

    Arguments:
        key (str) - name of the file as it will appear in the bucket
    
    Returns:
        str - full URL that a client can use to load the file into the system
    """
    url = minio_client.presigned_put_object(
        bucket_name='documents',  # TODO: <--- This hardcoded value is not ideal
        object_name=key,
        expires=timedelta(minutes=10),
    )
    return url
