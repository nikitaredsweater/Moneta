"""
Super small service that simply works with postgres to update the maturity time
in the database.

In the future this could be extneded into more functional service of events
that occur based on time.
"""
import asyncio, os, logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/moneta")
SLEEP_SECONDS = int(os.getenv("SLEEP_SECONDS", "3600")) # Do the check every hour
LOCK_KEY = int(os.getenv("LOCK_KEY", "90201"))
STATUS_ACTIVE = "ACTIVE"
STATUS_MATURED = "MATURED"

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("scheduler")

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
    engine = create_async_engine(DB_URL, pool_pre_ping=True)
    while True:
        try:
            # 1) acquire lock on its own connection (AUTOCOMMIT)
            async with engine.connect() as lock_conn:
                lock_ac = await lock_conn.execution_options(isolation_level="AUTOCOMMIT")
                got = await lock_ac.scalar(LOCK_SQL, {"k": LOCK_KEY})
                if not got:
                    log.debug("skip: lock held by another worker")
                else:
                    try:
                        # 2) do work on a separate connection/transaction
                        async with engine.begin() as tx_conn:
                            await tx_conn.execute(UPDATE_SQL, {
                                "new_status": STATUS_MATURED,
                                "old_status": STATUS_ACTIVE,
                            })
                            log.info("maturity tick executed")
                    finally:
                        # 3) always unlock via the SAME lock_conn (AUTOCOMMIT)
                        await lock_ac.execute(UNLOCK_SQL, {"k": LOCK_KEY})
        except Exception as e:
            log.exception("maturity tick failed: %s", e)

        await asyncio.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    asyncio.run(main())


# TODO: Add a check for whether the maturity settlement was reached or not?