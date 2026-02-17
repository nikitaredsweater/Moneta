#!/bin/bash
set -e

# ============================================================
# 1. Auto-generate JWT RSA keys if paths are not already set
# ============================================================
if [ -z "$JWT_PRIVATE_KEY_PATH" ] || [ -z "$JWT_PUBLIC_KEY_PATH" ]; then
    echo "[ENTRYPOINT] Generating ephemeral RSA key pair for JWT..."

    KEY_DIR="/tmp/jwt_keys"
    mkdir -p "$KEY_DIR"

    python3 -c "
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend(),
)

private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

public_pem = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)

with open('/tmp/jwt_keys/private.pem', 'wb') as f:
    f.write(private_pem)

with open('/tmp/jwt_keys/public.pem', 'wb') as f:
    f.write(public_pem)

print('[ENTRYPOINT] RSA keys generated successfully')
"

    export JWT_PRIVATE_KEY_PATH="/tmp/jwt_keys/private.pem"
    export JWT_PUBLIC_KEY_PATH="/tmp/jwt_keys/public.pem"

    echo "[ENTRYPOINT] JWT_PRIVATE_KEY_PATH=$JWT_PRIVATE_KEY_PATH"
    echo "[ENTRYPOINT] JWT_PUBLIC_KEY_PATH=$JWT_PUBLIC_KEY_PATH"
else
    echo "[ENTRYPOINT] Using provided JWT key paths"
fi

# ============================================================
# 2. Run Alembic migrations
# ============================================================
echo "[ENTRYPOINT] Running Alembic migrations..."
alembic upgrade head
echo "[ENTRYPOINT] Migrations complete"

# ============================================================
# 3. Start uvicorn
# ============================================================
echo "[ENTRYPOINT] Starting uvicorn on port ${PORT:-8080}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
