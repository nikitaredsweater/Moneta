"""
Models for actual document DTOs, mainly for user requests and responses
"""

from datetime import date

from app.enums import DocumentType
from app.schemas.base import BaseDTO, CamelModel


class DocumentUploadRequest(CamelModel):
    """
    Schema to request document upload
    """

    document_type: DocumentType
    extension: str


class DocumentAccessRequest(CamelModel):
    """
    Schema to request document access by exact name
    """

    document_name: str


class DocumentVersionUploadRequest(CamelModel):
    """
    Schema to request upload of a new document version
    """

    document_name: str
    extension: str
