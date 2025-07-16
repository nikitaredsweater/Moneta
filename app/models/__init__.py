"""
ORM
SQLAlchemy models and metadata for migration autogeneration.

You can import entities from here as orm.User to avoid collision
with schemas module.
"""

from app.models.user import User

__all__ = [
    'User',
]
