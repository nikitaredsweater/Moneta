"""
This module contains the functions to interact with the documents table.

All of the interaction with the documents table should be done through
this module.
"""

from typing import Annotated

from app import models, schemas
from app.repositories.base import BasePGRepository
from app.utils.session import async_session
from fastapi import Depends


class DocumentRepository(BasePGRepository[schemas.Document]):
    class Meta:
        response_model = schemas.Document  # This should be your schema
        orm_model = models.Document  # This should be your ORM model
        exclusion_fields = None


Document = Annotated[
    DocumentRepository,
    Depends(DocumentRepository.make_fastapi_dep(async_session)),
]
