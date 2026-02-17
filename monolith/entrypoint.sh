#!/bin/bash
set -e

# ============================================================
# 1. Set up JWT keys
#    Priority: base64 env vars > file path env vars > auto-generate
# ============================================================
KEY_DIR="/tmp/jwt_keys"

if [ -n "$JWT_PRIVATE_KEY_B64" ] && [ -n "$JWT_PUBLIC_KEY_B64" ]; then
    # Railway / production: decode base64-encoded keys from env vars
    echo "[ENTRYPOINT] Decoding JWT keys from base64 environment variables..."
    mkdir -p "$KEY_DIR"
    echo "$JWT_PRIVATE_KEY_B64" | base64 -d > "$KEY_DIR/private.pem"
    echo "$JWT_PUBLIC_KEY_B64" | base64 -d > "$KEY_DIR/public.pem"
    export JWT_PRIVATE_KEY_PATH="$KEY_DIR/private.pem"
    export JWT_PUBLIC_KEY_PATH="$KEY_DIR/public.pem"
    echo "[ENTRYPOINT] JWT keys decoded successfully"

elif [ -n "$JWT_PRIVATE_KEY_PATH" ] && [ -n "$JWT_PUBLIC_KEY_PATH" ]; then
    # Local dev with docker-compose: key file paths already set
    echo "[ENTRYPOINT] Using provided JWT key paths"

else
    # Fallback: auto-generate ephemeral keys (tokens invalidated on redeploy)
    echo "[ENTRYPOINT] Generating ephemeral RSA key pair for JWT..."
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

    export JWT_PRIVATE_KEY_PATH="$KEY_DIR/private.pem"
    export JWT_PUBLIC_KEY_PATH="$KEY_DIR/public.pem"
fi

echo "[ENTRYPOINT] JWT_PRIVATE_KEY_PATH=$JWT_PRIVATE_KEY_PATH"
echo "[ENTRYPOINT] JWT_PUBLIC_KEY_PATH=$JWT_PUBLIC_KEY_PATH"

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
