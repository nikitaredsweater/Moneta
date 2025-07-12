## Run migrations

1. Go to `root`
2. Run `alembic upgrade head`

## Create migration

1. Go to `root`
2. Run `alembic revision --autogenerate -m "{commit_message}"`

## Adding new model

1. Create models in `app/models`
2. Import models in `app/utils/database.py` to ensure they're included in Base.metadata
