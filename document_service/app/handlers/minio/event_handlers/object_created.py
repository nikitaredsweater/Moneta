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

logger = logging.getLogger(__name__)


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
    logger.debug(
        '[BUSINESS] Handling ObjectCreated:Put | bucket=%s | object_key=%s',
        event.bucket_name,
        event.object_key,
    )

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
                '[BUSINESS] Object key is None | bucket=%s',
                event.bucket_name,
            )
            return

        # The structure of object_key is set in the
        # app.utils.file_upload.py generate_secure_key
        user_id = object_key_parts[1]
        internal_filename = event.filename or 'unnamed'

        # Step 1: Check if document already exists
        logger.debug(
            '[BUSINESS] Checking document existence | filename=%s',
            internal_filename,
        )

        try:
            get_resp = await client.get_document(
                internal_filename=internal_filename
            )

            if get_resp.status == get_resp.GetStatus.FOUND:
                # Document exists, only create a new version
                logger.info(
                    '[BUSINESS] Document exists, creating new version | document_id=%s | filename=%s',
                    get_resp.document_id,
                    internal_filename,
                )
                document_id = get_resp.document_id

            elif get_resp.status == get_resp.GetStatus.NOT_FOUND:
                # Document doesn't exist, create it first
                logger.info(
                    '[BUSINESS] Document not found, creating new | filename=%s | user_id=%s',
                    internal_filename,
                    user_id,
                )

                doc_resp = await client.save_document(
                    internal_filename=internal_filename,
                    mime=event.mime or 'application/octet-stream',
                    storage_bucket=event.bucket_name or 'documents',
                    storage_object_key=event.object_key or '',
                    created_by=user_id,
                    created_at=event.event_time_dt,
                )

                logger.info(
                    '[BUSINESS] Document created | filename=%s | status=%s | document_id=%s',
                    internal_filename,
                    doc_resp.status,
                    doc_resp.row_id,
                )

                if doc_resp.status in [
                    doc_resp.CreateStatus.CREATED,
                    doc_resp.CreateStatus.ALREADY_EXISTS,
                ]:
                    document_id = doc_resp.row_id
                else:
                    logger.error(
                        '[BUSINESS] Document creation failed | filename=%s | message=%s',
                        internal_filename,
                        doc_resp.message,
                    )
                    return

            else:
                logger.error(
                    '[BUSINESS] Document existence check failed | filename=%s | message=%s',
                    internal_filename,
                    get_resp.message,
                )
                return

        except Exception as e:
            logger.error(
                '[BUSINESS] Error checking document existence | filename=%s | error_type=%s | error=%s',
                internal_filename,
                type(e).__name__,
                str(e),
            )
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
                '[BUSINESS] Document version created | document_id=%s | version_id=%s | status=%s',
                document_id,
                version_resp.version_id,
                version_resp.status,
            )

        except Exception as e:
            logger.error(
                '[BUSINESS] Error creating document version | document_id=%s | error_type=%s | error=%s',
                document_id,
                type(e).__name__,
                str(e),
            )
            return
