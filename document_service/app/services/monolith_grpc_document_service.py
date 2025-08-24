"""
Handles all tasks for communication with the gRPC on the monolith
"""
from app.clients import MonolithGrpcClient
import logging
from app.utils.minio_event_parsing import MinIOEvent
import app.gen.document_ingest_pb2 as pb

logger = logging.getLogger()

async def handle_new_document_creation(event:MinIOEvent):
    """
    Handles creation of a new document in the database. Alongside with
    registering the document in the database, it also stores the initial
    version of that document.
    """

    # TODO: For now this method only does the dummy request
    # Update the proto
    # Handle errors
    # Connect user_id into the whole thing

    async with MonolithGrpcClient(
        # target='monolith.internal:50061',
        metadata=[('authorization', 'Bearer <token>')],
        timeout_sec=3.0,
    ) as client:
        
        # Retrieving the company id and user id from the object key for now
        # TODO: In the future use redis to temporary store the user id in association with the object path
        object_key_parts = []
        if event.object_key:
            object_key_parts = event.object_key.split('/')
        else:
            logger.error("event.object_key should not be set to None but it is")
            return
        
        # The structure of object_key is set in the app.utils.file_upload.py generate_secure_key
        user_id = object_key_parts[1]

        resp = await client.save_document(
            internal_filename=event.filename or "unnamed",
            mime=event.mime or "application/octet-stream",
            storage_bucket=event.bucket_name or "documents",
            storage_object_key=event.object_key or "",
            created_by=user_id,
            created_at=event.event_time_dt,  # falls back to now() in client if None
        )
        # Handle CREATED / ALREADY_EXISTS as your app's success states:
        logger.info(
            f'Received gRPC respone: {resp.status}, {resp.row_id}, {resp.message}'
        )

        # TODO: Add a check that the previous command has sucessfully executed

        if event.version_id is None:
            event.version_id = ""

        resp_ver = await client.save_document_version(
            document_id=resp.row_id,
            version_number=1, # Deafult, but should use the actual version from the event
            storage_version_id=event.version_id,
            created_by=user_id,
            created_at=event.event_time_dt
        )

        logger.info(
            f'Received gRPC respone: {resp_ver.status}, {resp_ver.version_id}, {resp_ver.message}'
        )

