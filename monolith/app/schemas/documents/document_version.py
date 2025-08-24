"""
Document Version DTOs
"""

from datetime import datetime
from typing import Optional

from app.schemas.base import BaseDTO, MonetaID, CamelModel
from pydantic import Field


class DocumentVersion(BaseDTO):
    """
    Base Operation Document Version DTO
    """

    document_id: MonetaID
    version_number: int = Field(..., ge=1)
    storage_version_id: str  # internal version number id
    updated_at: Optional[datetime] = None # When set to deleted
    active: bool = True
    created_by: MonetaID # user who created this version

class DocumentVersionCreate(CamelModel):
    """
    Document Version Create
    """
    document_id: MonetaID
    version_number: int = Field(..., ge=1)
    storage_version_id: str  # internal version number id
    updated_at: Optional[datetime] = None
    active: bool = True
    created_by: MonetaID # user who created this version
    created_at: datetime = Field(default_factory=datetime.now)
