## Run migrations

1. Go to `root`
2. Run `alembic upgrade head`

## Adding new model

1. Create models in `app/models`
2. Update `combine_metadata` function with new model metadata

## Create migration

1. Go to `root`
2. Run `alembic revision --autogenerate -m "{commit_message}"`
