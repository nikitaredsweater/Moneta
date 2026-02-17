"""
Super small service that simply works with postgres to update the maturity time
in the database.

In the future this could be extneded into more functional service of events
that occur based on time.
"""
import asyncio
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from moneta_logging import configure_logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Configure logging from environment variables (LOG_LEVEL, LOG_OUTPUT, LOG_FILE_PATH)
# See moneta_logging package or docs/logging.md for logging rules and standards
configure_logging()

logger = logging.getLogger(__name__)

_raw_db_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/moneta",
)
# Railway provides postgresql:// but asyncpg needs postgresql+asyncpg://
if _raw_db_url.startswith("postgresql://"):
    DB_URL = _raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _raw_db_url.startswith("postgresql+psycopg://"):
    DB_URL = _raw_db_url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
else:
    DB_URL = _raw_db_url
SLEEP_SECONDS = int(os.getenv("SLEEP_SECONDS", "3600"))  # Do the check every hour
LOCK_KEY = int(os.getenv("LOCK_KEY", "90201"))
STATUS_ACTIVE = "ACTIVE"
STATUS_MATURED = "MATURED"

LOCK_SQL   = text("SELECT pg_try_advisory_lock(:k)")
UNLOCK_SQL = text("SELECT pg_advisory_unlock(:k)")
UPDATE_SQL = text("""
  UPDATE instruments
  SET instrument_status = :new_status
  WHERE instrument_status = :old_status
    AND maturity_date <= CURRENT_DATE
    AND deleted_at IS NULL
""")

async def main() -> None:
    logger.info('[SYSTEM] Scheduler service starting | sleep_interval_seconds=%d', SLEEP_SECONDS)
    engine = create_async_engine(DB_URL, pool_pre_ping=True)
    logger.info('[SYSTEM] Database engine created | pool_pre_ping=True')

    while True:
        try:
            # 1) acquire lock on its own connection (AUTOCOMMIT)
            async with engine.connect() as lock_conn:
                lock_ac = await lock_conn.execution_options(isolation_level="AUTOCOMMIT")
                got = await lock_ac.scalar(LOCK_SQL, {"k": LOCK_KEY})
                if not got:
                    logger.debug('[SYSTEM] Skipping tick | reason=lock held by another worker | lock_key=%d', LOCK_KEY)
                else:
                    try:
                        # 2) do work on a separate connection/transaction
                        async with engine.begin() as tx_conn:
                            result = await tx_conn.execute(UPDATE_SQL, {
                                "new_status": STATUS_MATURED,
                                "old_status": STATUS_ACTIVE,
                            })
                            logger.info('[DATABASE] Maturity tick executed | rows_affected=%d', result.rowcount)
                    finally:
                        # 3) always unlock via the SAME lock_conn (AUTOCOMMIT)
                        await lock_ac.execute(UNLOCK_SQL, {"k": LOCK_KEY})
        except Exception as e:
            logger.error('[DATABASE] Maturity tick failed | error_type=%s | error=%s', type(e).__name__, str(e))

        await asyncio.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())


# TODO: Add a check for whether the maturity settlement was reached or not?