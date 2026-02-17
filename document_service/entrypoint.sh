#!/bin/bash
set -e

# ============================================================
# 1. Set up JWT public key (verification only)
#    Priority: base64 env var > file path env var
# ============================================================
KEY_DIR="/tmp/jwt_keys"

if [ -n "$JWT_PUBLIC_KEY_B64" ]; then
    # Railway / production: decode base64-encoded public key from env var
    echo "[ENTRYPOINT] Decoding JWT public key from base64 environment variable..."
    mkdir -p "$KEY_DIR"
    echo "$JWT_PUBLIC_KEY_B64" | base64 -d > "$KEY_DIR/public.pem"
    export JWT_PUBLIC_KEY_PATH="$KEY_DIR/public.pem"
    echo "[ENTRYPOINT] JWT public key decoded successfully"

elif [ -n "$JWT_PUBLIC_KEY_PATH" ]; then
    # Local dev with docker-compose: key file path already set
    echo "[ENTRYPOINT] Using provided JWT public key path"

else
    echo "[ENTRYPOINT] WARNING: No JWT public key configured. Token verification will fail."
fi

echo "[ENTRYPOINT] JWT_PUBLIC_KEY_PATH=${JWT_PUBLIC_KEY_PATH:-<not set>}"

# ============================================================
# 2. Start uvicorn
# ============================================================
echo "[ENTRYPOINT] Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
