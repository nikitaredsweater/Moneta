"""
This module contains the functions to interact with the user table.
All of the interaction with the user table should be done through this module.
"""

from typing import Annotated

from app import models, schemas
from app.repositories.base import BasePGRepository
from app.utils.session import async_session
from fastapi import Depends


class CompanyRepository(BasePGRepository[schemas.Company]):
    class Meta:
        response_model = schemas.Company  # This should be your schema
        orm_model = models.Company  # This should be your ORM model
        exclusion_fields = None
        # When loading instruments, also eagerly load their public_payload
        nested_eager_relations = {
            "instruments": ["public_payload"],
        }


Company = Annotated[
    CompanyRepository,
    Depends(CompanyRepository.make_fastapi_dep(async_session)),
]
