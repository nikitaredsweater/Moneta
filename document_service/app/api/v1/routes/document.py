"""
Routes for uploading and downloading the actual documents, not metadata.
"""

import logging

from app.enums import DocumentType
from app.schemas import (
    DocumentAccessRequest,
    DocumentUploadRequest,
    DocumentVersionUploadRequest,
)
from app.services import (
    generate_presigned_download_url,
    generate_presigned_upload_url,
    generate_presigned_url,
)
from app.utils import generate_secure_key
from fastapi import APIRouter

logger = logging.getLogger(__name__)

document_router = APIRouter()

# Hardcoded values for development (will be replaced with proper auth later)
HARDCODED_USER_ID = '70b30fbc-3856-4f2f-89cd-c1c5688ca7c9'
HARDCODED_COMPANY_ID = 'company-1234'


# TODO: Add a permissions check and etc
@document_router.post('/upload/request')
async def request_upload_link(document_data: DocumentUploadRequest):
    """
    Gets you a link needed to directly upload the file.
    Step 1/2 to upload the file into the system.

    This is a system-blocking call, meaning it is not dealt with in a queue,
    to allow user to actually get the upload link.
    """
    logger.debug(
        '[BUSINESS] Upload link requested | extension=%s | user_id=%s',
        document_data.extension,
        HARDCODED_USER_ID,
    )

    # Generate a secure key for the new document
    key = generate_secure_key(
        user_id=HARDCODED_USER_ID,
        extension=document_data.extension,
        company_id=HARDCODED_COMPANY_ID,
    )

    # Save the key on the redis DB? <-- skipping this for now

    # Creating the upload link in minIO
    upload_url = generate_presigned_upload_url(key)

    logger.info(
        '[BUSINESS] Upload link generated | key=%s | user_id=%s',
        key,
        HARDCODED_USER_ID,
    )

    return {'key': upload_url}


@document_router.post('/access/request')
async def request_access_link(document_data: DocumentAccessRequest):
    """
    Gets you a link to access/download a document by its exact name.

    This endpoint provides a presigned download URL for documents stored in MinIO.
    """
    logger.debug(
        '[BUSINESS] Access link requested | document_name=%s | user_id=%s',
        document_data.document_name,
        HARDCODED_USER_ID,
    )

    # Create the full object key using the same structure as uploads
    # For exact name access, we use the provided document name directly
    key = f'{HARDCODED_COMPANY_ID}/{HARDCODED_USER_ID}/{document_data.document_name}'

    # Generate presigned download URL
    download_url = generate_presigned_download_url(key)

    logger.info(
        '[BUSINESS] Access link generated | document_name=%s | user_id=%s',
        document_data.document_name,
        HARDCODED_USER_ID,
    )

    return {'access_url': download_url}


@document_router.post('/version/upload/request')
async def request_version_upload_link(
    document_data: DocumentVersionUploadRequest,
):
    """
    Gets you a link to upload a new version of an existing document.

    This creates a new versioned upload for an existing document by name.
    The new version will be stored with a version-specific key.
    """
    logger.debug(
        '[BUSINESS] Version upload link requested | document_name=%s | user_id=%s',
        document_data.document_name,
        HARDCODED_USER_ID,
    )

    key = f'{HARDCODED_COMPANY_ID}/{HARDCODED_USER_ID}/{document_data.document_name}'

    # Create versioned upload URL
    upload_url = generate_presigned_upload_url(key)

    logger.info(
        '[BUSINESS] Version upload link generated | document_name=%s | user_id=%s',
        document_data.document_name,
        HARDCODED_USER_ID,
    )

    return {
        'upload_url': upload_url,
    }
