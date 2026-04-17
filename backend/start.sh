#!/usr/bin/env bash
# Root-level start script for Render deployment.
# Render always runs the start command from the repo root,
# so we explicitly cd into the backend directory first.
set -e

BACKEND_DIR="$(cd "$(dirname "$0")/backend" && pwd)"
echo "==> Starting from: $BACKEND_DIR"
echo "==> Python: $(python --version)"

export PYTHONPATH="$BACKEND_DIR"
cd "$BACKEND_DIR"

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
