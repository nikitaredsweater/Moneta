import asyncio
import os
import random
from datetime import date, datetime, timedelta, timezone
from typing import Sequence

import typer
from app.enums import (
    AddressType,
    InstrumentStatus,
    MaturityStatus,
    TradingStatus,
    UserRole,
)
from app.models import Company, CompanyAddress, Instrument, User
from app.security import encrypt_password
from faker import Faker
from sqlalchemy import select, text
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
    url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/moneta"
    )
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


# ----- instrument value helpers -----
def _rand_currency() -> str:
    return random.choice(["USD", "EUR", "GBP", "CHF", "RSD"])


def _gen_instrument_name(i: int) -> str:
    return f"INV-{datetime.now().strftime('%Y%m%d')}-{i:04d}-{random.randint(100,999)}"


def _pick_instrument_status() -> InstrumentStatus:
    # Heavily bias toward ACTIVE
    bag = [InstrumentStatus.ACTIVE] * 6 + [InstrumentStatus.DRAFT] * 3
    if hasattr(InstrumentStatus, "REJECTED"):
        bag += [InstrumentStatus.REJECTED]
    return random.choice(bag)


def _pick_maturity_status(maturity_dt: date) -> MaturityStatus:
    today = date.today()
    if maturity_dt > today + timedelta(days=7):
        return MaturityStatus.NOT_DUE
    if today <= maturity_dt <= today + timedelta(days=7):
        return (
            MaturityStatus.IN_GRACE
            if hasattr(MaturityStatus, "IN_GRACE")
            else MaturityStatus.NOT_DUE
        )
    # Past due
    # Prefer LATE/OVERDUE if present; fall back to DUE
    if hasattr(MaturityStatus, "LATE"):
        return MaturityStatus.LATE
    return MaturityStatus.DUE


def _pick_trading_status(readiness: InstrumentStatus) -> TradingStatus:
    if readiness == InstrumentStatus.ACTIVE:
        base = [
            TradingStatus.LISTED,
            TradingStatus.OFF_MARKET,
            TradingStatus.PAUSED,
        ]
        if hasattr(TradingStatus, "UNDER_OFFER"):
            base += [TradingStatus.UNDER_OFFER]
        return random.choice(base)
    # Not active -> shouldn't be openly listed
    return random.choice([TradingStatus.OFF_MARKET, TradingStatus.DRAFT])


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
            # we need IDs for FKs
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

            # Flush to ensure user/company IDs are available for FK assignment
            await session.flush()

            # Collect FK pools (robust even if models add constraints later)
            company_ids = [
                row[0]
                for row in (await session.execute(select(Company.id))).all()
            ]
            user_ids = [
                row[0] for row in (await session.execute(select(User.id))).all()
            ]
            if not company_ids or not user_ids:
                raise RuntimeError(
                    "Seeder prerequisite not met: companies and users must exist before instruments."
                )

            # --- Instruments (Receivables) ---
            today = date.today()
            for i in range(instruments):
                # Business values
                face_value = float(random.randrange(10_000, 250_000, 500))
                currency = _rand_currency()
                maturity_dt = today + timedelta(days=random.randint(-30, 360))
                # A simple premium component (ensure >= face value)
                maturity_payment = round(
                    face_value * (1.00 + random.uniform(0.02, 0.15)), 2
                )

                readiness = _pick_instrument_status()
                payout = _pick_maturity_status(maturity_dt)
                trading = _pick_trading_status(readiness)

                inst = Instrument(
                    name=_gen_instrument_name(i),
                    face_value=face_value,
                    currency=currency,
                    maturity_date=maturity_dt,
                    maturity_payment=maturity_payment,
                    instrument_status=readiness,
                    maturity_status=payout,
                    trading_status=trading,
                    issuer_id=random.choice(company_ids),
                    created_by=random.choice(user_ids),
                    created_at=datetime.now(timezone.utc),
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
