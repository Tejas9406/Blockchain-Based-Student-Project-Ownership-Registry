# Local IPFS (Kubo) Development & Integration Guide

> **Target Module**: Module 3 — Blockchain & Decentralized Storage (Developer 3)  
> **Component**: IPFS Decentralized Storage Adapter (`IPFSStorageAdapter`)  
> **Status**: Step 5.1 — IPFS Storage Foundation

---

## 1. Overview & Architecture

The registry uses IPFS (InterPlanetary File System) for decentralized, tamper-proof persistence of student project artifacts:
1. **Raw Artifacts**: Pinned as content-addressed files, returning individual IPFS CIDs (`ipfs_cid`).
2. **Project Versions**: Multiple project artifacts are assembled into a directory DAG, producing a single root directory CID (`ipfs_root_cid`) anchored on-chain.

```
Artifact Ingestion / Versioning
            │
            ▼
     StorageService
            │
    ┌───────┴────────────────────────┐
    ▼                                ▼
LocalStorageAdapter           IPFSStorageAdapter (Step 5.1)
(Development/Tests)                  │
                              HTTP POST /api/v0/*
                                     ▼
                              IPFS Kubo Node (Port 5001)
```

---

## 2. Environment Configuration

IPFS settings are environment-driven via `.env` or system environment variables:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `IPFS_API_URL` | `http://127.0.0.1:5001` | Kubo RPC API endpoint for add, cat, and pin calls |
| `IPFS_GATEWAY_URL` | `http://127.0.0.1:8080` | Public / local gateway URL for content retrieval |
| `IPFS_TIMEOUT_SECONDS` | `30` | Timeout threshold for IPFS network and node operations |
| `STORAGE_BACKEND` | `local` | Active backend: `local` (filesystem) or `ipfs` (Kubo node) |

> [!CAUTION]
> Never hardcode Pinata API keys, Web3.Storage tokens, or private endpoints in source code.

---

## 3. Running Local IPFS Kubo Daemon

To run a local Kubo node for end-to-end development:

### Option A: Binary Installation (Recommended)
1. Download Kubo from [https://dist.ipfs.tech/#kubo](https://dist.ipfs.tech/#kubo).
2. Initialize and start the daemon:
   ```bash
   ipfs init
   ipfs daemon
   ```
3. Verify the node is responding:
   ```bash
   curl -X POST http://127.0.0.1:5001/api/v0/version
   ```

### Option B: Docker
```bash
docker run -d --name ipfs-node \
  -p 4001:4001 -p 5001:5001 -p 8080:8080 \
  ipfs/kubo:latest
```

---

## 4. CID & Directory DAG Strategy

1. **Genuine CIDs**:
   - The adapter strictly returns genuine CIDs produced by the IPFS node (`CIDv0` starting with `Qm...` or `CIDv1` starting with `bafy...`).
   - Synthetic or fake CIDs are prohibited.
2. **Directory DAG Creation (`add_directory`)**:
   - Artifacts for a version are sent with `wrap-with-directory=true`.
   - Returns a mapping of all artifact filenames to their individual CIDs, as well as the root DAG directory CID (`root` / `""`) stored as `ipfs_root_cid`.
3. **Retrieval**:
   - `cat(cid_or_path)` and `cat_stream(cid_or_path)` allow reading content directly from the node.

---

## 5. Security Controls & Failure Behavior

- **SSRF Prevention**: The IPFS API URL is loaded strictly from server configuration. Client requests cannot supply arbitrary IPFS endpoints.
- **CID Sanitization**: All input CIDs are validated against strict regex before dispatch to `/api/v0/*`.
- **Node Failures**: If the Kubo node is unreachable or times out, the adapter raises `IPFSException` (HTTP 502 Bad Gateway), preventing partial state corruption or silent failures.

---

## 6. Testing Strategy

- **Unit Tests (`tests/test_ipfs.py`)**:
  - Test the adapter against simulated Kubo HTTP responses using `unittest.mock` / `respx` / `httpx.MockTransport`.
  - Zero external daemon dependency for standard test runs.
- **Integration Tests**:
  - Point `IPFS_API_URL` to a running Kubo instance to verify live pinning.
