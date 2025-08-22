"""
Document DTOs
"""

from datetime import datetime
from typing import Optional

from app.schemas.base import BaseDTO, CamelModel, MonetaID
from pydantic import Field

class Document(BaseDTO):
    """
    Base Operation Document DTO
    """

    internal_filename: str
    mime: str
    storage_bucket: str
    storage_object_key: str
    created_by: MonetaID
    updated_at: Optional[datetime]


class DocumentCreate(CamelModel):
    """
    Model for document creation
    """

    internal_filename: str
    mime: str
    storage_bucket: str
    storage_object_key: str
    created_by: MonetaID
    created_at: datetime = Field(default_factory=datetime.now)
