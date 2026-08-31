#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${ROOT_DIR}/blockchain"
echo "Starting Local Hardhat EVM Node on http://127.0.0.1:8545..."
npx hardhat node
