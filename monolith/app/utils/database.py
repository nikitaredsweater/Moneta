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

_MONGO_CLIENT: AsyncIOMotorClient | None = None
MONGO_CONNECTION_STRING = os.getenv('MONGO_URL', 'mongodb://mongodb:27017')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'moneta')


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


def _get_mongo_client() -> AsyncIOMotorClient:
    """
    Return a singleton Motor client.

    We keep one client per process (recommended by Motor) instead of
    opening/closing it on every request.
    """
    global _MONGO_CLIENT
    if _MONGO_CLIENT is None:
        _MONGO_CLIENT = AsyncIOMotorClient(MONGO_CONNECTION_STRING)
    return _MONGO_CLIENT


async def get_mongo_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    FastAPI dependency that yields an async MongoDB database.

    Yields:
        AsyncIOMotorDatabase: The MongoDB database object.
    """
    client = _get_mongo_client()
    db: AsyncIOMotorDatabase = client[MONGO_DB_NAME]
    yield db
