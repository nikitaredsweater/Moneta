"""
This module contains the functions to interact with the entity for Public Instrument Representation.
All of the interaction with the user table should be done through this module.
"""

from typing import Annotated

from app import models, schemas
from app.repositories.base import BasePGRepository
from app.utils.session import async_session
from fastapi import Depends


class InstrumentPublicPayloadRepository(BasePGRepository[schemas.InstrumentPublicPayloadFull]):
    class Meta:
        response_model = schemas.InstrumentPublicPayloadFull  # This should be your schema
        orm_model = models.InstrumentPublicPayload  # This should be your ORM model
        exclusion_fields = None


InstrumentPublicPayload = Annotated[
    InstrumentPublicPayloadRepository,
    Depends(InstrumentPublicPayloadRepository.make_fastapi_dep(async_session)),
]
