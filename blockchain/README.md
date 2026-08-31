# Blockchain Module — Developer 3 Guide

> **Module Owner**: Developer 3  
> **Stack**: Solidity 0.8.24, Hardhat, Ethers.js v6, Hardhat Toolbox, TypeScript, TypeChain  
> **Phase**: Phase 0 (Environment Foundation)

---

## 1. Directory Structure

```
blockchain/
├── contracts/            # Solidity smart contracts
│   └── HealthCheck.sol   # Diagnostic test contract
├── scripts/              # Deployment and network interaction scripts
│   └── deploy_healthcheck.ts
├── test/                 # Hardhat Mocha/Chai tests
│   └── HealthCheck.test.ts
├── hardhat.config.ts     # Network and compiler configuration
├── package.json          # Dependencies & scripts
├── tsconfig.json         # TypeScript configuration
└── README.md             # This document
```

---

## 2. Setup & Development

### 2.1 Prerequisites
- Node.js `v18+` or `v20+`
- npm `v9+`

### 2.2 Installation
```bash
cd blockchain
npm install
```

### 2.3 Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

---

## 3. Compiling & Testing Smart Contracts

```bash
# Compile contracts and generate TypeChain bindings
npm run compile
# or: npx hardhat compile

# Run the test suite on local Hardhat EVM
npm test
# or: npx hardhat test
```

---

## 4. Running a Local Standalone Blockchain Node

To run a standalone local node with 20 pre-funded test accounts:
```bash
npx hardhat node
```
This starts an RPC endpoint at `http://127.0.0.1:8545`.

In a separate terminal, deploy the diagnostic contract:
```bash
npx hardhat run scripts/deploy_healthcheck.ts --network localhost
```

---

## 5. Developer Rules for Blockchain & IPFS

1. **Off-Chain vs On-Chain Storage Principle**: Never store complete raw project files, codebases, or PDFs directly on-chain. Only cryptographic digests (SHA-256 hashes, IPFS CIDs), timestamps, and ownership state are stored on-chain.
2. **Deterministic Gas Optimization**: Ensure contracts are written with gas-efficient data structures (events, mappings, packed storage).
3. **Never Commit Private Keys**: Always use local simulated accounts for development. Keep testnet private keys strictly in `.env`.
4. **Follow Blockchain Design**: Refer to `docs/blockchain/BLOCKCHAIN_DESIGN.md` for upcoming contract specifications.
