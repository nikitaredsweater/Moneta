#!/bin/bash
set -e

echo "[ENTRYPOINT] Starting scheduler service..."
exec python -m scheduler.main
