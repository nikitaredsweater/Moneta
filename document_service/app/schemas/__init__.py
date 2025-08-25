"""
DTO Schemas entrypoint.
"""

from app.schemas.document import (
    DocumentAccessRequest,
    DocumentUploadRequest,
    DocumentVersionUploadRequest,
)

__all__ = [
    'DocumentUploadRequest',
    'DocumentAccessRequest',
    'DocumentVersionUploadRequest',
]
