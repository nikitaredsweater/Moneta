"""
This module contains the functions to interact with the user table.
All of the interaction with the user table should be done through this module.
"""

from typing import Annotated, Optional

from fastapi import Depends

from app import models, schemas
from app.repositories.base import BasePGRepository
from app.utils.session import async_session


class UserRepository(BasePGRepository[schemas.User]):
    class Meta:
        response_model = schemas.User  # This should be your schema
        orm_model = models.User  # This should be your ORM model
        exclusion_fields = None  # Optional: set fields to exclude


User = Annotated[
    UserRepository, Depends(UserRepository.make_fastapi_dep(async_session))
]
