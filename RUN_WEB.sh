#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "[Atlas Web] Validating..."
python -m py_compile \
    interfaces/web/runtime.py \
    interfaces/web/server.py

echo "[Atlas Web] Starting on 0.0.0.0:8000"
exec uvicorn interfaces.web.server:app \
    --host 0.0.0.0 \
    --port 8000
