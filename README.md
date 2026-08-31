# Blockchain-Based Student Project Ownership Registry

> **SIH 2026 Problem Statement**: `CYB05`  
> **Development Phase**: **Phase 0 — Development Environment & Monorepo Foundation Setup**  
> **Status**: Ready for Isolated 3-Developer Collaboration

---

## 1. Project Overview

The **Blockchain-Based Student Project Ownership Registry** is a decentralized, tamper-resistant platform designed to empower students and academic institutions to establish indisputable proof of intellectual property and academic project creation. 

By capturing project snapshots (ideas, designs, source code, and documentation), generating cryptographic SHA-256 digests, storing raw artifacts via decentralized storage (IPFS), and anchoring verifiable cryptographic proofs onto an Ethereum-compatible blockchain, the system provides immutable timestamped provenance, version tracking, and instant verification via verifiable certificates and QR codes.

---

## 2. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React, Vite, TypeScript, Tailwind CSS, React Router, Axios, Vitest | Responsive web interface & verification portal |
| **Backend** | Python 3.13+, FastAPI, Pydantic, SQLAlchemy, Alembic, Web3.py, Pytest | High-performance RESTful API & blockchain orchestration |
| **Database** | PostgreSQL 16 | Relational application metadata and user state |
| **Blockchain** | Solidity 0.8.24, Hardhat, Local Hardhat Network, Ethers.js | Smart contract ownership registry and cryptographic proof anchoring |
| **Decentralized Storage** | IPFS *(Integration planned in Phase 2)* | Content-addressable decentralized artifact storage |
| **DevOps & Containers** | Docker, Docker Compose | Reproducible multi-service development environments |

---

## 3. Architecture Overview

```
                          ┌───────────────────────────┐
                          │   Frontend (React + Vite) │
                          └─────────────┬─────────────┘
                                        │ HTTP / JSON
                                        ▼
                          ┌───────────────────────────┐
                          │   Backend (FastAPI REST)  │
                          └───┬───────────┬─────────┬─┘
                              │           │         │
                   SQLAlchemy │           │ IPFS    │ Web3.py
                              ▼           │ Client  ▼
                    ┌────────────┐        │  ┌───────────────────────┐
                    │ PostgreSQL │        │  │ Smart Contracts       │
                    │ (Metadata) │        │  │ (Proof & Anchoring)   │
                    └────────────┘        │  └───────────┬───────────┘
                                          ▼              │
                                   ┌─────────────┐       ▼
                                   │ IPFS Node   │  ┌─────────────────────────┐
                                   │ (Artifacts) │  │ Ethereum-Compatible EVM │
                                   └─────────────┘  └─────────────────────────┘
```

- **PostgreSQL**: Stores relational metadata (users, project summaries, tags, audit logs).
- **IPFS**: Stores project documents, code bundles, and visual artifacts off-chain.
- **Blockchain**: Stores minimal, immutable cryptographic hashes (SHA-256 / CID), timestamps, and ownership records to ensure low gas costs and infinite tamper resistance.

---

## 4. Repository Structure

```
student-project-ownership-registry/
├── frontend/                     # React + Vite client (Developer 1)
│   ├── src/
│   │   ├── components/           # UI components
│   │   ├── pages/                # Route views (Health/Environment shell)
│   │   ├── services/             # Axios API client
│   │   ├── tests/                # Vitest unit tests
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
│
├── backend/                      # FastAPI service (Developer 2)
│   ├── app/
│   │   ├── core/                 # Settings & logging
│   │   ├── database/             # SQLAlchemy engine & session
│   │   ├── models/               # Database ORM models (placeholder)
│   │   ├── schemas/              # Pydantic schemas (health response)
│   │   ├── routers/              # API endpoints (/health)
│   │   ├── services/             # Business logic layer (placeholder)
│   │   ├── utils/                # Helper utilities
│   │   └── main.py               # FastAPI entrypoint
│   ├── alembic/                  # Database migration scripts
│   ├── tests/                    # Pytest test suite
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   └── README.md
│
├── blockchain/                   # Hardhat & Solidity (Developer 3)
│   ├── contracts/                # Solidity contracts (HealthCheck placeholder)
│   ├── scripts/                  # Deployment & verification scripts
│   ├── test/                     # Hardhat Mocha/Chai tests
│   ├── hardhat.config.ts
│   ├── package.json
│   └── README.md
│
├── docs/                         # Architecture & Technical Specs
│   ├── architecture/             # System architecture & data flow
│   ├── api/                      # API contract specifications
│   ├── database/                 # Domain model & database design
│   ├── blockchain/               # Smart contract design & verification model
│   └── development/              # 3-Developer workflow guide
│
├── scripts/                      # Cross-platform development utilities
│   ├── setup/                    # Environment bootstrap scripts
│   ├── dev/                      # Service startup scripts
│   └── test/                     # Test orchestration scripts
│
├── tests/
│   └── integration/              # End-to-end and cross-module integration tests
│
├── docker-compose.yml            # Multi-container orchestration
├── .gitignore                    # Comprehensive ignore rules
├── .env.example                  # Root environment template
├── CONTRIBUTING.md               # Branch strategy and PR checklist
└── README.md                     # This file
```

---

## 5. Prerequisites

Ensure you have the following installed on your development workstation:

1. **Node.js**: `v18.0.0` or later (Recommended: `v20+` or `v22+`)
2. **Python**: `3.11+` (Recommended: `3.12` or `3.13`)
3. **Git**: `2.30+`
4. **Docker & Docker Compose**: (Optional for local mode, required for containerized mode)

---

## 6. Quickstart: Development Setup

### 6.1 Clone & Configure Environment

```bash
git clone <repository-url>
cd Blockchain-Based-Student-Project-Ownership-Registry

# Copy root environment file
cp .env.example .env

# Configure submodules
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
cp blockchain/.env.example blockchain/.env
```

### 6.2 Automatic Dependency Installation

Run the unified setup script:
- **Windows (PowerShell)**:
  ```powershell
  .\scripts\setup\setup_all.ps1
  ```
- **Linux / macOS (Bash)**:
  ```bash
  chmod +x scripts/setup/*.sh scripts/test/*.sh
  ./scripts/setup/setup_all.sh
  ```

---

## 7. Running the Modules

### Option A: Running with Docker Compose (Recommended for Full Stack)

```bash
# Start PostgreSQL, Backend, and Frontend
docker compose up -d

# View logs
docker compose logs -f

# Stop containers
docker compose down
```

- **Frontend**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **PostgreSQL**: `localhost:5432`

---

### Option B: Running Modules Locally (Individual Developer Mode)

#### 1. Running Frontend (Developer 1)
```bash
cd frontend
npm install
npm run dev
# Running on http://localhost:5173
```

#### 2. Running Backend (Developer 2)
```bash
cd backend
python -m venv .venv

# Activate venv:
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Running on http://localhost:8000
```

#### 3. Running Blockchain Node & Tests (Developer 3)
```bash
cd blockchain
npm install

# Run tests
npx hardhat test

# Start local blockchain node
npx hardhat node
```

---

## 8. Running Automated Tests

Run tests across all three modules:

### Unified Test Runner
- **Windows (PowerShell)**:
  ```powershell
  .\scripts\test\run_all_tests.ps1
  ```
- **Linux / macOS (Bash)**:
  ```bash
  ./scripts/test/run_all_tests.sh
  ```

### Individual Test Suites
- **Frontend Test**:
  ```bash
  cd frontend && npm test
  ```
- **Backend Test**:
  ```bash
  cd backend && pytest
  ```
- **Blockchain Test**:
  ```bash
  cd blockchain && npx hardhat test
  ```

---

## 9. Developer Responsibilities & Collaboration

| Role | Focus Area | Key Documents |
| :--- | :--- | :--- |
| **Developer 1** | UI/UX, Component Architecture, Client Routing, API Integration | `frontend/README.md`, `docs/api/API_CONTRACT.md` |
| **Developer 2** | API Routes, Database Schemas, Alembic Migrations, Services | `backend/README.md`, `docs/database/DATABASE_DESIGN.md` |
| **Developer 3** | Smart Contracts, Gas Optimization, Hardhat Tests, IPFS | `blockchain/README.md`, `docs/blockchain/BLOCKCHAIN_DESIGN.md` |

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/development/WORKFLOW.md](docs/development/WORKFLOW.md) for full branch policies and collaboration rules.

---

## 10. Current Phase & Roadmap

- [x] **Phase 0: Monorepo Foundation & Multi-Developer Environment Setup** (Current)
- [ ] **Phase 1: Domain Modeling, PostgreSQL Schemas & Core Smart Contract Implementation**
- [ ] **Phase 2: IPFS Artifact Ingestion & Web3.py Blockchain Anchoring Service**
- [ ] **Phase 3: React Frontend Views, Verification Portal & QR/Certificate Engine**
- [ ] **Phase 4: End-to-End Integration, Security Auditing & Deployment**
