#!/usr/bin/env bash
# Root-level start script — used if render.yaml startCommand is set to: bash start.sh
set -e
BACKEND_DIR="/opt/render/project/src/backend"
export PYTHONPATH="$BACKEND_DIR"
cd "$BACKEND_DIR"
echo "==> Starting from $(pwd) with Python $(python --version)"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
