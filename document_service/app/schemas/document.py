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


# TODO: Maybe I need to make a new model without the created_at field
class DocumentDownloadRequest(BaseDTO):
    """
    Schema to request document download
    """
