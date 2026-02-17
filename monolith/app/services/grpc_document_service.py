"""
Document and Document Version Handlers.

This module contains asynchronous handler functions for performing operations
with documents and their versions. These handlers are typically invoked in
response to incoming gRPC requests and serve as an interface between the
transport layer (gRPC) and the persistence layer (repositories).

Responsibilities:
    - Creating new document records in the database
    - Adding and managing document versions
    - Retrieving documents by filename

All functions interact with the database via repository classes and rely on
async SQLAlchemy sessions.
"""

import logging
import uuid
from datetime import datetime

import app.models as models
import app.schemas as schemas
from app.repositories import DocumentRepository, DocumentVersionRepository
from app.utils.session import async_session

logger = logging.getLogger(__name__)


async def save_document(
    internal_filename: str,
    mime: str,
    storage_bucket: str,
    storage_object_key: str,
    created_by_user_id: uuid.UUID,
    created_at: datetime,
) -> schemas.Document:
    """
    Save a new document record in the database.

    This function registers a new document with its associated storage details.

    Args:
        internal_filename (str): Internal filename assigned by the system
        mime (str): MIME type of the document (e.g., "application/pdf")
        storage_bucket (str): Name of the storage bucket where the file resides
        storage_object_key (str): Object key/path of the file inside the bucket
        created_by_user_id (uuid.UUID): Identifier of the user who
            created/uploaded the document
        created_at (datetime): Timestamp of when the document was created

    Returns:
        schemas.Document: The newly created document schema object
    """
    logger.debug(
        '[BUSINESS] Saving document | filename=%s | mime=%s | bucket=%s',
        internal_filename,
        mime,
        storage_bucket,
    )
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
        created_at=created_at,
    )

    document_repo = DocumentRepository(async_session)
    doc = await document_repo.create(new_doc)
    logger.info(
        '[BUSINESS] Document saved | document_id=%s | filename=%s | created_by=%s',
        doc.id,
        internal_filename,
        created_by_user_id,
    )
    return doc


async def save_document_version(
    document_id: uuid.UUID,
    storage_version_id: str,
    created_by: uuid.UUID,
    created_at: datetime,
):
    """
    Add a new version record for an existing document.

    This function creates a new version entry for a given document,
    typically triggered when a file is updated or replaced in storage.

    Args:
        document_id (uuid.UUID): The unique identifier of the parent document.
        storage_version_id (str): Identifier of the version
            in the storage system (MinIO version ID)
        created_by (uuid.UUID): Identifier of the user who created this version
        created_at (datetime): Timestamp of when this version was created

    Returns:
        schemas.DocumentVersion: The newly created document
            version schema object
    """
    logger.debug(
        '[BUSINESS] Saving document version | document_id=%s | storage_version_id=%s',
        document_id,
        storage_version_id,
    )
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
        max_retries=3,
    )

    logger.info(
        '[BUSINESS] Document version saved | version_id=%s | document_id=%s | '
        'created_by=%s',
        version.id,
        document_id,
        created_by,
    )
    return version


async def get_document_by_filename(
    internal_filename: str,
) -> schemas.Document | None:
    """
    Retrieve a document by its internal filename.

    This function queries the database for a document record associated with
    the given internal filename. It is useful for resolving documents
    deterministically when the filename is unique in the system.

    Args:
        internal_filename (str): The internal filename assigned to the document

    Returns:
        schemas.Document | None:
            - The corresponding document schema object if found
            - None if no document matches the provided filename
    """
    logger.debug('[BUSINESS] Fetching document by filename | filename=%s', internal_filename)
    document_repo = DocumentRepository(async_session)

    # Use the get_one method with a where clause to find by internal_filename
    document = await document_repo.get_one(
        where_list=[models.Document.internal_filename == internal_filename]
    )

    if document:
        logger.info(
            '[BUSINESS] Document found | document_id=%s | filename=%s',
            document.id,
            internal_filename,
        )
    else:
        logger.warning('[BUSINESS] Document not found | filename=%s', internal_filename)

    return document
