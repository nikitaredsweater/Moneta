"""
Handler for minio events that match the regex
s3:ObjectCreated:*

That includes the following event list:
OBJECT_CREATED = [
    's3:ObjectCreated:CompleteMultipartUpload',
    's3:ObjectCreated:Copy',
    's3:ObjectCreated:DeleteTagging',
    's3:ObjectCreated:Post',
    's3:ObjectCreated:Put',
    's3:ObjectCreated:PutLegalHold',
    's3:ObjectCreated:PutRetention',
    's3:ObjectCreated:PutTagging',
]
"""

from __future__ import annotations

import logging

from app.clients import MonolithGrpcClient
from app.handlers.minio.registry import handles
from app.utils.minio_event_parsing import MinIOEvent

logger = logging.getLogger()


@handles('s3:ObjectCreated:Put')
async def handle_new_document_creation(event: MinIOEvent, raw: dict) -> None:
    """
    Handles the creation of a new document in the database upon receiving
    a MinIO event.

    Args:
        event (MinIOEvent): The event object containing information
            about the created object, including its filename, MIME type,
            and storage details.
        raw (dict): The raw event data from MinIO, which may contain
            additional metadata.

    Returns:
        None
    """

    async with MonolithGrpcClient(
        metadata=[('authorization', 'Bearer <token>')],
        timeout_sec=3.0,
    ) as client:

        # Retrieving the company id and user id from the object key for now
        # TODO: In the future use redis to temporary store the
        # user id in association with the object path

        object_key_parts = []
        if event.object_key:
            object_key_parts = event.object_key.split('/')
        else:
            logger.error(
                'event.object_key should not be \
                set to None but it is.'
            )
            return

        # The structure of object_key is set in the
        # app.utils.file_upload.py generate_secure_key
        user_id = object_key_parts[1]
        internal_filename = event.filename or 'unnamed'

        # Step 1: Check if document already exists
        logger.info(
            'Checking if document exists with internal_filename: %s',
            internal_filename,
        )

        try:
            get_resp = await client.get_document(
                internal_filename=internal_filename
            )

            if get_resp.status == get_resp.GetStatus.FOUND:
                # Document exists, only create a new version
                logger.info(
                    'Document found with ID: %s. Creating new version.',
                    get_resp.document_id,
                )
                document_id = get_resp.document_id

            elif get_resp.status == get_resp.GetStatus.NOT_FOUND:
                # Document doesn't exist, create it first
                logger.info('Document not found. Creating new document.')

                doc_resp = await client.save_document(
                    internal_filename=internal_filename,
                    mime=event.mime or 'application/octet-stream',
                    storage_bucket=event.bucket_name or 'documents',
                    storage_object_key=event.object_key or '',
                    created_by=user_id,
                    created_at=event.event_time_dt,
                )

                logger.info(
                    'Document creation response: %s, %s, %s',
                    doc_resp.status,
                    doc_resp.row_id,
                    doc_resp.message,
                )

                if doc_resp.status in [
                    doc_resp.CreateStatus.CREATED,
                    doc_resp.CreateStatus.ALREADY_EXISTS,
                ]:
                    document_id = doc_resp.row_id
                else:
                    logger.error(
                        'Failed to create document: %s', doc_resp.message
                    )
                    return

            else:
                logger.error(
                    'Failed to check document existence: %s', get_resp.message
                )
                return

        except Exception as e:
            logger.error('Error checking document existence: %s', e)
            return

        if event.version_id is None:
            event.version_id = ''

        try:
            version_resp = await client.save_document_version(
                document_id=document_id,
                version_number=1,
                storage_version_id=event.version_id,
                created_by=user_id,
                created_at=event.event_time_dt,
            )

            logger.info(
                'Document version creation response: %s, %s, %s, %s',
                version_resp.status,
                version_resp.version_id,
                version_resp.message,
            )

        except Exception as e:
            logger.error('Error creating document version: %s', e)
            return
