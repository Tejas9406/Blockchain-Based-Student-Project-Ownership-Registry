#!/usr/bin/env bash
# ==============================================================================
# Master Test Runner Script for Linux / macOS
# Executes test suites across Frontend, Backend, and Blockchain modules
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "================================================================"
echo "Student Project Ownership Registry — Monorepo Test Runner (Unix)"
echo "================================================================"

# 1. Frontend Tests
echo ""
echo "[1/3] Running Frontend Tests (Vitest)..."
cd "${ROOT_DIR}/frontend"
npm test

# 2. Backend Tests
echo ""
echo "[2/3] Running Backend Tests (pytest)..."
cd "${ROOT_DIR}/backend"
source .venv/bin/activate
pytest

# 3. Blockchain Tests
echo ""
echo "[3/3] Running Blockchain Smart Contract Tests (Hardhat)..."
cd "${ROOT_DIR}/blockchain"
npx hardhat test

echo ""
echo "================================================================"
echo "🎉 ALL TESTS PASSED SUCCESSFULLY! (Frontend, Backend, Blockchain)"
echo "================================================================"
