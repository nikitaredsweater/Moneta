"""
This module contains the functions to interact with the user table.
All of the interaction with the user table should be done through this module.
"""

from typing import Annotated

from fastapi import Depends

from app import models, schemas
from app.repositories.base import BasePGRepository
from app.utils.session import async_session


class CompanyAddressRepository(BasePGRepository[schemas.CompanyAddress]):
    class Meta:
        response_model = schemas.CompanyAddress  # This should be your schema
        orm_model = models.CompanyAddress  # This should be your ORM model
        exclusion_fields = None


CompanyAddress = Annotated[
    CompanyAddressRepository,
    Depends(CompanyAddressRepository.make_fastapi_dep(async_session)),
]
