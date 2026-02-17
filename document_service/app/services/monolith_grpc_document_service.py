"""
Handles all tasks for communication with the gRPC on the monolith.

This module provides service functions for interacting with the monolith's
gRPC document service.
"""

import logging

import app.gen.document_ingest_pb2 as pb
from app.clients import MonolithGrpcClient
from app.utils.minio_event_parsing import MinIOEvent

logger = logging.getLogger(__name__)


async def handle_new_document_creation(event: MinIOEvent):
    """
    Handles creation of a new document in the database.

    Alongside registering the document in the database, it also stores
    the initial version of that document.

    Args:
        event: MinIO event containing document information.
    """
    logger.debug(
        '[BUSINESS] Processing new document creation | object_key=%s | bucket=%s',
        event.object_key,
        event.bucket_name,
    )

    async with MonolithGrpcClient(
        metadata=[('authorization', 'Bearer <token>')],
        timeout_sec=3.0,
    ) as client:

        # Retrieving the company id and user id from the object key for now
        # TODO: In the future use redis to temporary store the user id
        # in association with the object path
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

        logger.info(
            '[BUSINESS] Creating document via gRPC | filename=%s | user_id=%s',
            internal_filename,
            user_id,
        )

        resp = await client.save_document(
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
            resp.status,
            resp.row_id,
        )

        # TODO: Add a check that the previous command has successfully executed

        if event.version_id is None:
            event.version_id = ''

        resp_ver = await client.save_document_version(
            document_id=resp.row_id,
            version_number=1,
            storage_version_id=event.version_id,
            created_by=user_id,
            created_at=event.event_time_dt,
        )

        logger.info(
            '[BUSINESS] Document version created | document_id=%s | version_id=%s | status=%s',
            resp.row_id,
            resp_ver.version_id,
            resp_ver.status,
        )

