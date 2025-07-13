"""
User ORM model
"""

from sqlalchemy import Column, String

from app.models.base import Base, BaseEntity


class User(Base, BaseEntity):
    """
    User profile
    """

    __tablename__ = 'users'

    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
