"""
Contains handlers for the operations with the documents and document versions.
Call these functions upon gRPC request beeing received.
"""

import uuid
from datetime import datetime

import app.models as models
import app.schemas as schemas
from app.repositories import DocumentRepository
from app.utils.session import async_session


async def save_document(
    internal_filename: str,
    mime: str,
    storage_bucket: str,
    storage_object_key: str,
    created_by_user_id: uuid.UUID,
    created_at: datetime
) -> schemas.Document:
    """
    Saves document in the database
    """
    # TODO: Add verifications.
    # Better, just add exception handling, since SQL Server will do all of the checks regardless

    new_doc = schemas.DocumentCreate(
        internal_filename=internal_filename,
        mime=mime,
        storage_bucket=storage_bucket,
        storage_object_key=storage_object_key,
        created_by=created_by_user_id,
        created_at=created_at
    )

    document_repo = DocumentRepository(async_session)
    doc = await document_repo.create(new_doc)
    return doc
