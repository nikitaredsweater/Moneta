"""
Database utilities and base classes.
"""

# FIXME: I do not know why, but something does not work here :(

# pylint: skip-file
# -1: [file-ignored]

import os
from typing import AsyncGenerator, Generator

from conf import conf
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Create SQLAlchemy engine for synchronous operations (used by alembic)
engine = create_engine(conf.connection_string)

# Create SessionLocal class for synchronous operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for all models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Get database session for synchronous operations.

    Yields:
        Session: A synchronous database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session.

    Yields:
        AsyncSession: An asynchronous database session.
    """
    # Import here to avoid circular import during alembic runs
    from app.utils.session import async_session

    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
