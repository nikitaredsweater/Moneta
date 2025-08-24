"""
Contains handlers for the operations with the documents and document versions.
Call these functions upon gRPC request beeing received.
"""

import uuid
from datetime import datetime

import app.models as models
import app.schemas as schemas
from app.repositories import DocumentRepository, DocumentVersionRepository
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
    # 
    # Better, just add exception handling, since SQL
    # Server will do all of the checks regardless

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


async def save_document_version(document_id:uuid.UUID,
                                version_number:int,
                                storage_version_id:str,
                                created_by:uuid.UUID,
                                created_at: datetime):
    """
    Adds to the database a record about a new version of the file
    (including the initial version).
    """
    # TODO: Add verifications.
    # 
    # Better, just add exception handling, since SQL
    # Server will do all of the checks regardless

    document_version_repository = DocumentVersionRepository(async_session)
    version = await document_version_repository.create_next_version(
        document_id=document_id,
        storage_version_id=storage_version_id,
        created_by=created_by,
        created_at=created_at,
        max_retries=3
    )

    return version
