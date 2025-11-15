import asyncio
import os
import random
from datetime import date, timedelta
from typing import Sequence

import typer
from app.enums import AddressType  # <-- adjust if needed; <-- adjust
from app.enums import InstrumentStatus, MaturityStatus, TradingStatus, UserRole
from app.models import CompanyAddress  # <-- adjust if needed
from app.models import Company, Instrument, User

# ==== import your project bits (adjust paths if needed) ====
from app.security import encrypt_password
from faker import Faker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

cli = typer.Typer(help="Seed the database with deterministic demo/test data.")


# ---------- helpers ----------
def require_non_prod() -> None:
    env = os.getenv("ENV", "dev").lower()
    if env in {"prod", "production"}:
        raise SystemExit("Refusing to seed in production (ENV=prod)")


def get_db_url() -> str:
    """
    Reads DATABASE_URL and ensures async driver.
    Works for both dev and test stacks (Option 2).
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit(
            "Set DATABASE_URL (e.g. postgresql+asyncpg://user:pass@host/db)"
        )
    if "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    return url


async def truncate_all(engine) -> None:
    """
    TRUNCATE in FK-safe order (adjust table names if needed).
    Uses CASCADE to be resilient to FK graphs.
    """
    statements: Sequence[str] = [
        "TRUNCATE TABLE instrument_events RESTART IDENTITY CASCADE",
        "TRUNCATE TABLE instruments RESTART IDENTITY CASCADE",
        "TRUNCATE TABLE company_addresses RESTART IDENTITY CASCADE",
        "TRUNCATE TABLE users RESTART IDENTITY CASCADE",
        "TRUNCATE TABLE companies RESTART IDENTITY CASCADE",
    ]
    async with engine.begin() as conn:
        for sql in statements:
            try:
                await conn.execute(text(sql))
            except Exception:
                # Table may not exist in early dev; ignore to keep seed robust
                pass


# ---------- main command ----------
@cli.command("run")
def run(
    companies: int = typer.Option(6, help="How many companies to create"),
    users: int = typer.Option(
        16, help="How many users to create (incl. 1 admin)"
    ),
    instruments: int = typer.Option(50, help="How many instruments to create"),
    reset: bool = typer.Option(
        True, help="TRUNCATE all domain tables before seeding"
    ),
    seed: int = typer.Option(42, help="Deterministic RNG seed"),
    verbose: bool = typer.Option(False, help="Verbose SQLAlchemy echo"),
):
    """
    Seed DB with coherent demo/test data.
    """
    require_non_prod()
    faker = Faker()
    Faker.seed(seed)
    random.seed(seed)

    db_url = get_db_url()
    engine = create_async_engine(db_url, echo=verbose, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async def _main():
        if reset:
            await truncate_all(engine)

        async with Session() as session:
            # --- Companies ---
            companies_created: list[Company] = []
            for i in range(companies):
                reg = f"{faker.msisdn()[:10]}-{i}"
                c = Company(
                    legal_name=faker.company(),
                    trade_name=faker.company_suffix(),
                    registration_number=reg,
                    incorporation_date=faker.date_between(
                        date(1995, 1, 1), date(2023, 12, 31)
                    ),
                )
                session.add(c)
                companies_created.append(c)
            await session.flush()

            # --- Addresses (1–3 per company) ---
            for c in companies_created:
                for _ in range(random.randint(1, 3)):
                    addr = CompanyAddress(
                        company_id=c.id,
                        type=random.choice(
                            [
                                AddressType.REGISTERED,
                                AddressType.OFFICE,
                                AddressType.BILLING,
                            ]
                        ),
                        street=faker.street_address(),
                        city=faker.city(),
                        state=faker.state_abbr(),
                        postal_code=faker.postcode(),
                        country="US",
                    )
                    session.add(addr)

            # --- Users ---
            # Admin you can log in with:
            admin = User(
                email="admin@example.com",
                password=encrypt_password("password123"),
                first_name="Admin",
                last_name="User",
                company_id=random.choice(companies_created).id,
                role=UserRole.ADMIN,
            )
            session.add(admin)

            # More users:
            for i in range(max(0, users - 1)):
                u = User(
                    email=f"user{i}@example.com",
                    password=encrypt_password("password123"),
                    first_name=faker.first_name(),
                    last_name=faker.last_name(),
                    company_id=random.choice(companies_created).id,
                    role=random.choice(
                        [UserRole.BUYER, UserRole.SELLER, UserRole.ISSUER]
                    ),
                )
                session.add(u)
            await session.flush()

            # --- Instruments (Receivables) ---
            today = date.today()
            for _ in range(instruments):
                maturity = today + timedelta(days=random.randint(30, 360))
                readiness = random.choices(
                    [
                        InstrumentStatus.ACTIVE,
                        InstrumentStatus.DRAFT,
                        InstrumentStatus.REJECTED,
                    ],
                    weights=[0.7, 0.25, 0.05],
                    k=1,
                )[0]
                payout = random.choice(
                    [
                        MaturityStatus.NOT_DUE,
                        MaturityStatus.DUE,
                        MaturityStatus.IN_GRACE,
                        MaturityStatus.PARTIALLY_PAID,
                        MaturityStatus.PAID,
                        MaturityStatus.LATE,
                    ]
                )
                trade_pool = (
                    [
                        TradingStatus.LISTED,
                        TradingStatus.OFF_MARKET,
                        TradingStatus.PAUSED,
                    ]
                    if readiness == InstrumentStatus.ACTIVE
                    else [TradingStatus.OFF_MARKET, TradingStatus.DRAFT]
                )
                trading = random.choice(trade_pool)

                inst = Instrument(
                    # fill required business fields on your model in addition to statuses:
                    # e.g., face_value=..., currency="USD", issuer_id=..., maturity_date=maturity, ...
                    readiness_status=readiness,
                    payout_status=payout,
                    trading_status=trading,
                )
                session.add(inst)

            await session.commit()

        print("\n✔ Seed complete")
        print(f"  Companies:   {companies}")
        print(
            f"  Users:       {users}  (login: admin@example.com / password123)"
        )
        print(f"  Instruments: {instruments}")

    asyncio.run(_main())


if __name__ == "__main__":
    cli()
