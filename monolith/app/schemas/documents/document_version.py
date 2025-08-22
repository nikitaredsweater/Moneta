"""
Document Version DTOs
"""

from datetime import datetime
from typing import Optional

from app.schemas.base import BaseDTO, MonetaID
from pydantic import Field


class DocumentVersion(BaseDTO):
    """
    Base Operation Document Version DTO
    """

    document_id: MonetaID
    version_number: int = Field(..., ge=1)
    storage_version_id: str  # internal version number id
    updated_at: Optional[datetime]
    active: bool = True
