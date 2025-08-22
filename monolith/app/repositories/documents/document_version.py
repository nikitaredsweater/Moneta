"""
This module contains the functions to interact with the document_versions table.

All of the interaction with the document_versions table should be done through
this module.
"""

from typing import Annotated

from app import models, schemas
from app.repositories.base import BasePGRepository
from app.utils.session import async_session
from fastapi import Depends


class DocumentVersionRepository(BasePGRepository[schemas.DocumentVersion]):
    class Meta:
        response_model = schemas.DocumentVersion  # This should be your schema
        orm_model = models.DocumentVersion  # This should be your ORM model
        exclusion_fields = None


DocumentVersion = Annotated[
    DocumentVersionRepository,
    Depends(DocumentVersionRepository.make_fastapi_dep(async_session)),
]
