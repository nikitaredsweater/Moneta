"""SQLAlchemy session"""

from conf import conf
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    conf.asyncpg_connection_string,
    pool_size=conf.pool_size,
    future=True,
    connect_args={'timeout': 1200},
)

async_session = sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)
