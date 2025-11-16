# Moneta Seeder (`app.seed.seed`)

Deterministically populate your **non-production** database with coherent demo/test data:
- Companies (+ addresses)
- Users (incl. a loginable admin)
- Instruments/Receivables with realistic fields and enum statuses

> Safety guard: the seeder refuses to run when `ENV` is set to `prod` / `production`.

---

## Quick Start

```bash
# From monolith working dir (virtualenv activated)
python -m app.seed.seed run --reset --companies 8 --users 20 --instruments 120
```

If you’re running Docker Compose (dev/test stacks), make sure your `DATABASE_URL` points at the right Postgres:

- **Inside containers** (service-to-service):  
  `postgresql+asyncpg://postgres:postgres@postgres:5432/moneta`

- **From your host (Mac/Linux/Windows)** talking to the Compose-exposed port:  
  `postgresql+asyncpg://postgres:postgres@localhost:5432/moneta`

Export first to avoid long commands:

```bash
export ENV=dev
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/moneta"
python -m app.seed.seed run --reset
```

---

## CLI

```
python -m app.seed.seed run [OPTIONS]
```

**Options (with defaults):**
- `--companies INTEGER` (default: `6`)  
  How many companies to create.

- `--users INTEGER` (default: `16`)  
  Total users, including one admin user created automatically.

- `--instruments INTEGER` (default: `50`)  
  How many receivables/instruments to create.

- `--reset / --no-reset` (default: `--reset`)  
  TRUNCATE domain tables (FK-safe, CASCADE) before seeding.

- `--seed INTEGER` (default: `42`)  
  RNG seed for fully reproducible data.

- `--verbose / --no-verbose` (default: `--no-verbose`)  
  Echo SQLAlchemy statements.

**Examples**
```bash
# Minimal run with defaults
python -m app.seed.seed run

# Heavier dataset, keep existing rows
python -m app.seed.seed run --no-reset --companies 20 --users 80 --instruments 500

# Deterministic dataset for screenshots/demos
python -m app.seed.seed run --reset --seed 123 --companies 10 --users 40 --instruments 200
```

---

## What gets generated

- **Companies** with basic registration metadata.
- **Company addresses** (1–3 per company) of types:
  `REGISTERED`, `OFFICE`, `BILLING`.
- **Users**
  - Admin: `admin@example.com` / `password123`
  - Additional users with roles from `{BUYER, SELLER, ISSUER}`.
- **Instruments (Receivables)** with required fields set:
  - `name`, `face_value`, `currency`, `maturity_date`, `maturity_payment`
  - `issuer_id` (FK to Company), `created_by` (FK to User)
  - Enum triplet: `instrument_status`, `maturity_status`, `trading_status`
  - `created_at` (UTC)

Statuses are chosen coherently (e.g., non-active instruments won’t appear as openly listed).

---

## Environment Variables

- `ENV`  
  Controls safety check. If `prod` or `production`, seeding aborts.

- `DATABASE_URL`  
  Target database. If it uses `postgresql://…`, the seeder auto-upgrades it to `postgresql+asyncpg://…`.

**Typical values**
```bash
# Dev in Docker (inside container network)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/moneta

# Dev from host
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/moneta

# Test database variant (if you run a parallel stack)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/moneta_test
```

---

## Running in Docker Compose (dev/test)

- Ensure your `postgres` service is up and healthy.
- From your **host**, use `localhost` in `DATABASE_URL`.
- From **inside a container**, use the service name `postgres`.

If you maintain a separate **test** stack (e.g., `moneta_test` DB), point `DATABASE_URL` there to keep test data isolated from dev data.

---

## Troubleshooting

**`ValueError: the greenlet library is required…`**  
Install greenlet for SQLAlchemy async internals:
```bash
pip install "sqlalchemy[asyncio]" greenlet asyncpg
```

**`gaierror: nodename nor servname provided, or not known`**  
Your `DATABASE_URL` host is wrong for where you run the command:
- Use `postgres` when running **inside** Docker network.
- Use `localhost` when running **on the host**.

**`NotNullViolationError` on instruments**  
You’re on an older seeder or changed model constraints. Update to the current `seed.py` which sets all required fields (name, face_value, currency, maturity_date, maturity_payment, issuer_id, created_by, and enums).

**Migrations / schema mismatch**  
Run Alembic before seeding:
```bash
alembic upgrade head
```

---

## Notes

- Seeding is **idempotent with `--reset`**: it truncates in a FK-safe order.
- The RNG `--seed` ensures repeatable datasets for screenshots & tests.
- The admin account is for quick UI login; rotate in real deployments.
- Never set `ENV=prod` for this script; it will hard-stop to protect prod.
- VERY IMPORTANT: Currently this script will populate the actual production database. That is fine up until the point we roll out a first real version of the code.
---
