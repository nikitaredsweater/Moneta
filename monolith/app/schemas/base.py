"""
Base data transfer object
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# Use Pydantic's UUID4 with a custom factory
MonetaID = Annotated[UUID, Field(default_factory=uuid4)]


def _to_camel(string: str) -> str:
    """
    Convert snake_case to camelCase

    Args:
        string (str): The string to convert

    Returns:
        str: The converted string
    """
    str_split = string.split("_")
    return str_split[0] + "".join(word.capitalize() for word in str_split[1:])


class CamelModel(BaseModel):
    """
    Base model that converts snake_case to camelCase
    """

    model_config = {
        'alias_generator': _to_camel,
        'populate_by_name': True,
    }


class BaseDTO(CamelModel):
    """
    Base Moneta Financial DTO

    This is a base class for all DTOs.
    It contains the id and created_at fields.
    It also converts snake_case to camelCase.

    Make sure that the DTO fields match the ORM model fields.

    Except for:
      deleted_at field.
    """

    id: MonetaID
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = {
        'from_attributes': True,  # Updated from orm_mode
        'alias_generator': _to_camel,
        'populate_by_name': True,
    }
