#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${ROOT_DIR}/frontend"
echo "Starting React Frontend dev server on http://localhost:5173..."
npm run dev
