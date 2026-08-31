#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${ROOT_DIR}/backend"
source .venv/bin/activate
echo "Starting FastAPI Backend server on http://localhost:8000..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
