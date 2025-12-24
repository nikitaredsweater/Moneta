"""
Routes for uploading and downloading the actual documents, not metadata.

All endpoints require JWT authentication and appropriate permissions.
User data is extracted from the JWT token claims.
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
from fastapi import APIRouter, Depends
from moneta_auth import (
    TokenClaims,
    Permission,
    PermissionVerb as Verb,
    PermissionEntity as Entity,
    has_permission,
    get_current_claims,
)

logger = logging.getLogger(__name__)

document_router = APIRouter()


@document_router.post('/upload/request')
async def request_upload_link(
    document_data: DocumentUploadRequest,
    claims: TokenClaims = Depends(get_current_claims()),
    _=Depends(has_permission([Permission(Verb.CREATE, Entity.DOCUMENT)])),
):
    """
    Gets you a link needed to directly upload the file.
    Step 1/2 to upload the file into the system.

    This is a system-blocking call, meaning it is not dealt with in a queue,
    to allow user to actually get the upload link.

    Requires: CREATE.DOCUMENT permission
    """
    user_id = claims.user_id
    company_id = claims.company_id or 'no-company'

    logger.debug(
        '[BUSINESS] Upload link requested | extension=%s | user_id=%s | company_id=%s',
        document_data.extension,
        user_id,
        company_id,
    )

    # Generate a secure key for the new document
    key = generate_secure_key(
        user_id=user_id,
        extension=document_data.extension,
        company_id=company_id,
    )

    # Creating the upload link in minIO
    upload_url = generate_presigned_upload_url(key)

    logger.info(
        '[BUSINESS] Upload link generated | key=%s | user_id=%s | company_id=%s',
        key,
        user_id,
        company_id,
    )

    return {'key': upload_url}


@document_router.post('/access/request')
async def request_access_link(
    document_data: DocumentAccessRequest,
    claims: TokenClaims = Depends(get_current_claims()),
    _=Depends(has_permission([Permission(Verb.VIEW, Entity.DOCUMENT)])),
):
    """
    Gets you a link to access/download a document by its exact name.

    This endpoint provides a presigned download URL for documents stored in MinIO.

    Requires: VIEW.DOCUMENT permission
    """
    user_id = claims.user_id
    company_id = claims.company_id or 'no-company'

    logger.debug(
        '[BUSINESS] Access link requested | document_name=%s | user_id=%s | company_id=%s',
        document_data.document_name,
        user_id,
        company_id,
    )

    # Create the full object key using the same structure as uploads
    # For exact name access, we use the provided document name directly
    key = f'{company_id}/{user_id}/{document_data.document_name}'

    # Generate presigned download URL
    download_url = generate_presigned_download_url(key)

    logger.info(
        '[BUSINESS] Access link generated | document_name=%s | user_id=%s | company_id=%s',
        document_data.document_name,
        user_id,
        company_id,
    )

    return {'access_url': download_url}


@document_router.post('/version/upload/request')
async def request_version_upload_link(
    document_data: DocumentVersionUploadRequest,
    claims: TokenClaims = Depends(get_current_claims()),
    _=Depends(has_permission([Permission(Verb.UPDATE, Entity.DOCUMENT)])),
):
    """
    Gets you a link to upload a new version of an existing document.

    This creates a new versioned upload for an existing document by name.
    The new version will be stored with a version-specific key.

    Requires: UPDATE.DOCUMENT permission
    """
    user_id = claims.user_id
    company_id = claims.company_id or 'no-company'

    logger.debug(
        '[BUSINESS] Version upload link requested | document_name=%s | user_id=%s | company_id=%s',
        document_data.document_name,
        user_id,
        company_id,
    )

    key = f'{company_id}/{user_id}/{document_data.document_name}'

    # Create versioned upload URL
    upload_url = generate_presigned_upload_url(key)

    logger.info(
        '[BUSINESS] Version upload link generated | document_name=%s | user_id=%s | company_id=%s',
        document_data.document_name,
        user_id,
        company_id,
    )

    return {
        'upload_url': upload_url,
    }
