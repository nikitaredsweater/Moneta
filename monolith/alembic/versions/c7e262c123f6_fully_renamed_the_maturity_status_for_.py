# pylint: skip-file
"""
fully renamed the maturity status for instruments

Revision ID: c7e262c123f6
Revises: a13ab065a013
Create Date: 2025-11-14 21:47:38.809487

"""
"""redefine payoutstatus enum

Revision ID: 2025_11_14_redefine_payoutstatus
Revises: <PUT_PREVIOUS_REVISION_ID_HERE>
Create Date: 2025-11-14

"""
import sqlalchemy as sa
from alembic import op

# ---------------------------------------------------------------------
# CONFIGURE THESE CONSTANTS FOR YOUR SCHEMA
# ---------------------------------------------------------------------

# The existing enum type name in Postgres (most ORMs create lowercase)
ENUM_NAME = "maturity_status"
# Temporary name for the new enum during the swap
ENUM_NAME_NEW = f"{ENUM_NAME}_new"
# Temporary name used during downgrade
ENUM_NAME_OLD = f"{ENUM_NAME}_old"

# If your enum lives in a non-public schema, set SCHEMA="your_schema"
SCHEMA = None  # or "public"

# All places where the enum is used: (table_name, column_name)
AFFECTED = [
    ("instruments", "maturity_status"),
    # If you store status in other tables, add them here:
    # ("instrument_events", "payout_status"),
]

# NEW enum values (exactly what you want after the redefinition)
NEW_VALUES = [
    "NOT_DUE",
    "DUE",
    "IN_GRACE",
    "PARTIALLY_PAID",
    "PAID",
    "LATE",
    "DEFAULTED",
    "DISPUTED",
]

# OLD enum values — only needed if you want a working downgrade.
# If you don't care about downgrade, you may leave as-is and no-op the downgrade.
OLD_VALUES = [
    # <<< FILL WITH YOUR PRIOR SET >>> e.g.
    # "NOT_DUE", "DUE", "PAID"
    'NOT_TRADING',
    'PENDING',
    'SETTLED',
    'DEFAULTED',
]

# Optional default for the column (as a string enum literal) or None to skip
# Example: DEFAULT_VALUE = "NOT_DUE"
DEFAULT_VALUE = "NOT_DUE"


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------
def qident(name: str) -> str:
    """Quote an identifier, with optional schema qualification."""
    if SCHEMA:
        return f'"{SCHEMA}"."{name}"'
    return f'"{name}"'


def qtype(name: str) -> str:
    """Qualified type name (schema.type) for DDL."""
    if SCHEMA:
        return f'{SCHEMA}.{name}'
    return name


def create_enum(name: str, values: list[str]):
    vals = ", ".join(f"'{v}'" for v in values)
    op.execute(f"CREATE TYPE {qtype(name)} AS ENUM ({vals})")


def drop_enum(name: str):
    op.execute(f"DROP TYPE {qtype(name)}")


# ---------------------------------------------------------------------
# Alembic identifiers
# ---------------------------------------------------------------------
revision = "c7e262c123f6"
down_revision = "a13ab065a013"
branch_labels = None
depends_on = None


def upgrade():
    # 1) Create the new enum type with the updated values
    create_enum(ENUM_NAME_NEW, NEW_VALUES)

    # 2) For every affected column: drop default, cast to new enum, restore default
    for table, col in AFFECTED:
        # Drop default (if any) to avoid cast errors
        op.execute(
            f"""
            ALTER TABLE {qident(table)}
            ALTER COLUMN "{col}" DROP DEFAULT
            """
        )
        # Cast through text to the new enum
        op.execute(
            f"""
            ALTER TABLE {qident(table)}
            ALTER COLUMN "{col}" TYPE {qtype(ENUM_NAME_NEW)}
            USING "{col}"::text::{qtype(ENUM_NAME_NEW)}
            """
        )
        # Optional: set a new default
        if DEFAULT_VALUE is not None:
            op.execute(
                f"""
                ALTER TABLE {qident(table)}
                ALTER COLUMN "{col}" SET DEFAULT '{DEFAULT_VALUE}'::{qtype(ENUM_NAME_NEW)}
                """
            )

    # 3) Drop the old enum type
    drop_enum(ENUM_NAME)

    # 4) Rename the new enum to the original name so ORM/type names remain stable
    op.execute(f'ALTER TYPE {qtype(ENUM_NAME_NEW)} RENAME TO {ENUM_NAME}')


def downgrade():
    # If you don't need downgrade, you can leave this function empty.
    if not OLD_VALUES:
        # No-op downgrade
        return

    # 1) Create a temporary enum with the OLD values
    create_enum(ENUM_NAME_OLD, OLD_VALUES)

    # 2) Cast columns back to OLD enum
    for table, col in AFFECTED:
        # Drop default first
        op.execute(
            f"""
            ALTER TABLE {qident(table)}
            ALTER COLUMN "{col}" DROP DEFAULT
            """
        )
        op.execute(
            f"""
            ALTER TABLE {qident(table)}
            ALTER COLUMN "{col}" TYPE {qtype(ENUM_NAME_OLD)}
            USING "{col}"::text::{qtype(ENUM_NAME_OLD)}
            """
        )
        # (Optionally) restore an old default if you had one before
        # Example:
        op.execute(
            f"""
            ALTER TABLE {qident(table)}
            ALTER COLUMN "{col}" SET DEFAULT 'NOT_TRADING'::{qtype(ENUM_NAME_OLD)}
            """
        )

    # 3) Drop the current (new) enum (now named ENUM_NAME)
    drop_enum(ENUM_NAME)

    # 4) Rename OLD back to original name
    op.execute(f'ALTER TYPE {qtype(ENUM_NAME_OLD)} RENAME TO {ENUM_NAME}')
