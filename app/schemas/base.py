"""
Base data transfer object
"""

import os
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MonetaID(UUID):
    """Moneta Financial ID. Set up as uuid4"""

    def __init__(self, from_str: Optional[str] = None) -> None:
        if from_str:
            super().__init__(from_str, version=4)
        else:
            super().__init__(bytes=os.urandom(16), version=4)


def _to_camel(string: str) -> str:
    """
    Convert snake_case to camelCase

    Args:
        string (str): The string to convert

    Returns:
        str: The converted string
    """
    str_split = string.split('_')
    return str_split[0] + ''.join(word.capitalize() for word in str_split[1:])


class CamelModel(BaseModel):
    """
    Base model that converts snake_case to camelCase
    """

    class Config:
        """
        Config for the model
        """

        alias_generator = _to_camel
        allow_population_by_field_name = True


class BaseDTO(CamelModel):
    """
    Base Moneta Financial DT

    This is a base class for all DTOs.
    It contains the id and created_at fields.
    It also converts snake_case to camelCase.O

    Make sure that the DTO fields match the ORM model fields.

    Except for:
      deleted_at field.
    """

    id: MonetaID = Field(default_factory=MonetaID)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        """
        Config for the model
        """

        orm_mode = True
