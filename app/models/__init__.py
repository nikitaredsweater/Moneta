"""
ORM
SQLAlchemy models and metadata for migration autogeneration.

You can import entities from here as orm.User to avoid collision
with schemas module.
"""

import warnings

from sqlalchemy import MetaData
from sqlalchemy import exc as sa_exc

from app.models.company import Company
from app.models.user import User

# __all__ = [
#     'User',
# ]


def combine_metadata(*args: MetaData) -> MetaData:
    m = MetaData()
    for metadata in args:
        for t in metadata.tables.values():
            t.tometadata(m)
    return m


with warnings.catch_warnings():
    warnings.simplefilter('ignore', category=sa_exc.SAWarning)
    combined_metadata = combine_metadata(User.metadata, Company.metadata)
