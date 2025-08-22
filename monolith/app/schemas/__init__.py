"""
DTO
Schemas entrypoint.

You can import entities from here as schemas.User to avoid collision
with models module.
"""

from app.schemas.company import Company, CompanyCreate
from app.schemas.company_address import CompanyAddress, CompanyAddressCreate
from app.schemas.documents.document import Document
from app.schemas.documents.document_version import DocumentVersion
from app.schemas.instrument import (
    Instrument,
    InstrumentCreate,
    InstrumentCreateInternal,
)
from app.schemas.user import (
    User,
    UserCreate,
    UserDelete,
    UserInternal,
    UserLogin,
    UserUpdate,
)

__all__ = [
    'User',
    'UserCreate',
    'UserUpdate',
    'UserDelete',
    'UserLogin',
    'Company',
    'CompanyCreate',
    'CompanyAddress',
    'CompanyAddressCreate',
    'UserInternal',
    'Instrument',
    'InstrumentCreate',
    'InstrumentCreateInternal',
    'Document',
    'DocumentVersion',
]
