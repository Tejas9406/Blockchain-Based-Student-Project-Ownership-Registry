# System Architecture Specification

> **Project**: Blockchain-Based Student Project Ownership Registry  
> **Problem Statement**: SIH 2026 CYB05  
> **Document Version**: 1.0 (Phase 0 Baseline)

---

## 1. High-Level Architecture Overview

The system is designed with a hybrid on-chain / off-chain architecture that maximizes cryptographic immutability, data availability, and cost efficiency.

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Layer (Developer 1)"]
        UI["React + Vite Single Page App"]
        Router["React Router Navigation"]
        Axios["Axios API Client"]
        UI --> Router --> Axios
    end

    subgraph APILayer ["Backend Orchestration Layer (Developer 2)"]
        FastAPI["FastAPI REST Application"]
        Pydantic["Pydantic Validation & Schemas"]
        AuthService["Auth & Session Service (Future)"]
        HashService["SHA-256 Digest Engine (Future)"]
        FastAPI --> Pydantic
        FastAPI --> AuthService
        FastAPI --> HashService
    end

    subgraph DataLayer ["Data & Storage Layer (Developer 2 & 3)"]
        PG[("PostgreSQL 16\n(Relational Metadata)")]
        IPFS["IPFS Decentralized Node\n(Raw Artifacts & Code)"]
    end

    subgraph BlockchainLayer ["Blockchain Layer (Developer 3)"]
        Web3Py["Web3.py Client"]
        SmartContract["Project Ownership Registry\n(Solidity EVM Contract)"]
        EVM["Ethereum-Compatible Blockchain\n(Hardhat Local / Polygon / Sepolia)"]
        
        Web3Py --> SmartContract --> EVM
    end

    Axios -->|"HTTP REST Requests"| FastAPI
    FastAPI -->|"SQLAlchemy ORM"| PG
    FastAPI -->|"Content Upload & CID Generation"| IPFS
    FastAPI -->|"Proof Anchoring & Verification"| Web3Py
```

---

## 2. Component Layer Responsibilities

### 2.1 Frontend (Client Layer)
- **Role**: Provides student registration portals, project submission interfaces, version provenance timelines, QR code verification viewers, and certificate export tools.
- **Boundaries**: Interacts exclusively with the FastAPI backend via structured REST endpoints. Does not talk directly to PostgreSQL or make raw unauthenticated Web3 calls for mutation.

### 2.2 Backend (FastAPI Layer)
- **Role**: Serves as the central orchestrator and business logic gateway.
- **Key Duties**:
  - Request validation and authorization.
  - Streaming file intake, calculating cryptographic SHA-256 hashes.
  - Offloading full artifacts to IPFS and receiving content identifiers (CIDs).
  - Calling smart contracts via Web3.py to anchor ownership records.
  - Generating verification certificates and signing verifiable credentials.

### 2.3 Storage Layer (Hybrid Off-Chain Model)

| Storage Engine | Purpose | Why This Choice? |
| :--- | :--- | :--- |
| **PostgreSQL 16** | Application metadata, user profiles, tags, categories, search indexes, relational audit logs. | Fast relational querying, indexing, and transactional integrity. |
| **IPFS (InterPlanetary File System)** | Raw project code files, documentation PDFs, design schematics, and presentation slides. | Content-addressable, decentralized, tamper-evident off-chain file storage. |
| **Ethereum / EVM Blockchain** | Cryptographic hash digests (SHA-256 / IPFS CID), author wallet addresses, timestamps, version numbers, dispute state. | Immutability, zero censorship, trustless independent verification. |

> [!IMPORTANT]
> **Zero File On-Chain Rule**: Storing large binary files on a blockchain is prohibitively expensive and causes chain bloat. In our architecture, **no files are stored on-chain**. Only fixed 32-byte cryptographic hashes and metadata pointers are anchored on-chain.

---

## 3. End-to-End Project Registration Data Flow (Planned for Phase 2)

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student / Developer
    participant UI as React Frontend
    participant API as FastAPI Backend
    participant DB as PostgreSQL
    participant IPFS as IPFS Node
    participant Chain as Blockchain (Smart Contract)

    Student->>UI: Submits project (Title, Abstract, Code ZIP / PDF)
    UI->>API: POST /api/v1/projects (Multipart form data)
    API->>API: Compute SHA-256 hash of all uploaded artifacts
    API->>IPFS: Upload artifacts & receive IPFS CID
    API->>Chain: Register Project(AuthorID, SHA256_Hash, IPFS_CID, Timestamp)
    Chain-->>API: Transaction receipt & on-chain Token/Record ID
    API->>DB: Save metadata, IPFS CID, Tx Hash, Record ID
    API-->>UI: Registration Success (Record ID, Tx Hash, Timestamp, QR payload)
    UI-->>Student: Display Proof Certificate & QR Code
```

---

## 4. Verification Workflow

Anyone (examiner, hackathon evaluator, recruiter, patent agent) can verify a project independently:

1. **Hash Verification**: The verifier uploads a project file or enters the project ID.
2. **On-Chain Query**: The backend/verifier queries the smart contract for the anchored hash and original creation timestamp.
3. **Integrity Match**: If `SHA256(Uploaded_File) == Anchored_OnChain_Hash`, proof of original creation and non-tampering is mathematically guaranteed.
