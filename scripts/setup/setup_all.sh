#!/usr/bin/env bash
# ==============================================================================
# Master Setup Script for Linux / macOS
# Installs dependencies for Frontend, Backend, and Blockchain modules
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${ROOT_DIR}"

echo "================================================================"
echo "Student Project Ownership Registry — Master Setup (Unix)"
echo "================================================================"

# 1. Environment Files Initialization
echo ""
echo "[1/4] Initializing Environment Variables (.env)..."
[ ! -f .env ] && cp .env.example .env && echo " -> Created root .env"
[ ! -f frontend/.env ] && cp frontend/.env.example frontend/.env && echo " -> Created frontend/.env"
[ ! -f backend/.env ] && cp backend/.env.example backend/.env && echo " -> Created backend/.env"
[ ! -f blockchain/.env ] && cp blockchain/.env.example blockchain/.env && echo " -> Created blockchain/.env"

# 2. Frontend Setup
echo ""
echo "[2/4] Installing Frontend Dependencies..."
cd "${ROOT_DIR}/frontend"
npm install

# 3. Backend Setup
echo ""
echo "[3/4] Setting up Backend Python Virtual Environment..."
cd "${ROOT_DIR}/backend"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Blockchain Setup
echo ""
echo "[4/4] Installing Blockchain Dependencies..."
cd "${ROOT_DIR}/blockchain"
npm install

cd "${ROOT_DIR}"
echo ""
echo "================================================================"
echo "Master Setup Completed Successfully!"
echo "================================================================"
