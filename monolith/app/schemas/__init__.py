"""
DTO
Schemas entrypoint.

You can import entities from here as schemas.User to avoid collision
with models module.
"""

from app.schemas.base import MonetaID
from app.schemas.company import Company, CompanyCreate, CompanyFilters
from app.schemas.company_address import CompanyAddress, CompanyAddressCreate
from app.schemas.documents.document import Document, DocumentCreate
from app.schemas.documents.document_version import (
    DocumentVersion,
    DocumentVersionCreate,
)
from app.schemas.instrument import (
    Instrument,
    InstrumentCreate,
    InstrumentCreateInternal,
)
from app.schemas.user import (
    User,
    UserCreate,
    UserDelete,
    UserFilters,
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
    'UserFilters',
    'Company',
    'CompanyCreate',
    'CompanyFilters',
    'CompanyAddress',
    'CompanyAddressCreate',
    'UserInternal',
    'Instrument',
    'InstrumentCreate',
    'InstrumentCreateInternal',
    'Document',
    'DocumentCreate',
    'DocumentVersion',
    'DocumentVersionCreate',
    'MonetaID',
]
