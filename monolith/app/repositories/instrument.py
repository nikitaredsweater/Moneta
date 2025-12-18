"""
This module contains the functions to interact with the instruments table.
All of the interaction with the user table should be done through this module.
"""

from typing import Annotated

from fastapi import Depends
import logging

from app import models, schemas
from app.repositories.base import BasePGRepository
from app.utils.session import async_session

logger = logging.getLogger()


class InstrumentRepository(BasePGRepository[schemas.Instrument]):
    class Meta:
        response_model = schemas.Instrument  # This should be your schema
        orm_model = models.Instrument  # This should be your ORM model
        exclusion_fields = None
        eager_relations = [models.Instrument.public_payload]

Instrument = Annotated[
    InstrumentRepository,
    Depends(InstrumentRepository.make_fastapi_dep(async_session)),
]
