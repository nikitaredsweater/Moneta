"""
ORM
SQLAlchemy models and metadata for migration autogeneration.

You can import entities from here as orm.User to avoid collision
with schemas module.
"""

import warnings

from app.models.ask import Ask
from app.models.bid import Bid
from app.models.company import Company
from app.models.company_address import CompanyAddress
from app.models.documents.document import Document
from app.models.documents.document_version import DocumentVersion
from app.models.documents.instrument_document import InstrumentDocument
from app.models.instrument import Instrument
from app.models.instrument_ownership import InstrumentOwnership
from app.models.instrument_public_payload import InstrumentPublicPayload
from app.models.listing import Listing
from app.models.user import User
from sqlalchemy import MetaData
from sqlalchemy import exc as sa_exc

__all__ = [
    'User',
    'Company',
    'CompanyAddress',
    'InstrumentPublicPayload',
    'InstrumentDocument',
    'InstrumentOwnership',
    'Listing',
    'Bid',
    'Ask',
]


def combine_metadata(*args: MetaData) -> MetaData:
    m = MetaData()
    for metadata in args:
        for t in metadata.tables.values():
            t.tometadata(m)
    return m


with warnings.catch_warnings():
    warnings.simplefilter('ignore', category=sa_exc.SAWarning)
    combined_metadata = combine_metadata(
        User.metadata,
        Company.metadata,
        CompanyAddress.metadata,
        Instrument.metadata,
        Document.metadata,
        DocumentVersion.metadata,
        InstrumentPublicPayload.metadata,
        InstrumentDocument.metadata,
        InstrumentOwnership.metadata,
        Listing.metadata,
        Bid.metadata,
        Ask.metadata,
    )
