#!/bin/bash
set -e

# Write JWT keys from environment variable content to files.
# On Railway (or any cloud env), set JWT_PRIVATE_KEY and JWT_PUBLIC_KEY
# as secret env vars containing the full PEM content.
# JWT_PRIVATE_KEY_PATH and JWT_PUBLIC_KEY_PATH will be set automatically.

if [ -n "$JWT_PRIVATE_KEY" ]; then
    mkdir -p app/keys
    printf '%s' "$JWT_PRIVATE_KEY" > app/keys/jwt_private.pem
    export JWT_PRIVATE_KEY_PATH=app/keys/jwt_private.pem
fi

if [ -n "$JWT_PUBLIC_KEY" ]; then
    mkdir -p app/keys
    printf '%s' "$JWT_PUBLIC_KEY" > app/keys/jwt_public.pem
    export JWT_PUBLIC_KEY_PATH=app/keys/jwt_public.pem
fi

# Run database migrations before starting the app
alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8080
