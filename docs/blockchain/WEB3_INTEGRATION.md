# Web3.py Blockchain Integration Layer

**Module**: SIH 2026 — CYB05: Blockchain-Based Student Project Ownership Registry  
**Integration Boundary**: FastAPI Backend ↔ `ProjectRegistry.sol` (EVM)  
**Implementation**: `backend/app/services/blockchain_service.py`  

---

## 1. Architecture Overview

The Web3 integration layer connects the Python/FastAPI backend to the Ethereum/EVM execution layer hosting `ProjectRegistry.sol`. It encapsulates all JSON-RPC transport, transaction signing, gas estimation, and ABI encoding behind a clean service layer.

```
┌───────────────────────────────────────────────────────────┐
│                   FastAPI Application                     │
│  (Routers: projects.py, verification.py, health.py)       │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│                      Service Layer                        │
│    (project_version_service.py, verification_service.py)   │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│                    BlockchainService                      │
│            (app.services.blockchain_service)             │
│   - Address Normalization & EIP-55 Checksumming           │
│   - SHA-256 Digest ↔ bytes32 Mapping                     │
│   - Enum Normalization (Lifecycle & Dispute Stages)       │
│   - Gas Price & EIP-1559 Strategy                         │
│   - Relayer Signing & Nonce Handling                      │
│   - Confirmation Depth Tracking                           │
│   - Event Log Processing & Decoding                       │
└─────────────────────────────┬─────────────────────────────┘
                              │ Web3.py 7.x (HTTPProvider)
                              ▼
┌───────────────────────────────────────────────────────────┐
│                     EVM RPC Node                          │
│        (Local Hardhat / Sepolia Testnet RPC)             │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│                  ProjectRegistry.sol                      │
│              (Immutable On-Chain Registry)                │
└───────────────────────────────────────────────────────────┘
```

---

## 2. Configuration Parameters

Configuration is managed via Pydantic `BaseSettings` (`backend/app/core/config.py`) and loaded from environment variables:

| Environment Variable | Type | Default | Description |
|---|---|---|---|
| `BLOCKCHAIN_RPC_URL` | `str` | `http://127.0.0.1:8545` | EVM JSON-RPC provider HTTP endpoint |
| `PROJECT_REGISTRY_CONTRACT_ADDRESS` | `str` | `""` | Deployed `ProjectRegistry` contract address |
| `BLOCKCHAIN_CHAIN_ID` | `int` | `31337` | Expected EVM network chain ID (31337 for Hardhat) |
| `RELAYER_PRIVATE_KEY` | `str` | `""` | Hex-encoded private key of authorized platform relayer |
| `BLOCKCHAIN_CONFIRMATION_BLOCKS` | `int` | `1` | Required confirmation depth before anchor finality |
| `BLOCKCHAIN_TIMEOUT_SECONDS` | `int` | `30` | RPC and transaction receipt timeout |

> [!CAUTION]
> **Zero Private Key Exposure**: `RELAYER_PRIVATE_KEY` must never be hardcoded, committed to git, or stored in PostgreSQL. It is loaded exclusively into memory on process startup.

---

## 3. Gas Relayer Model

In traditional dApps, end users must possess cryptocurrency to submit transactions. In this architecture, students do not pay gas or manage cryptocurrency keys:
1. Student authors create and freeze their project versions via the authenticated FastAPI interface.
2. The platform's **Gas Relayer Account** (`RELAYER_PRIVATE_KEY`) signs the `registerProjectVersion` transaction on-chain as `msg.sender`.
3. The smart contract validates `msg.sender == relayer || msg.sender == owner()`.
4. The smart contract records the student's Ethereum address (`author`) and co-authors (`coAuthors`) directly inside the immutable `VersionProof` record.
5. The relayer wallet address can be reassigned by the contract owner via `setRelayer(address)`.

---

## 4. Controlled ABI Loading

To ensure that the backend application does not depend on the Hardhat TypeScript source tree at runtime:
1. **Canonical Backend ABI**: A controlled copy of `ProjectRegistry.json` is maintained at `backend/app/abi/ProjectRegistry.json`.
2. **Dual-Path Loader**: `app.abi.get_project_registry_abi()` reads from `backend/app/abi/ProjectRegistry.json` first, falling back to `blockchain/artifacts/contracts/ProjectRegistry.sol/ProjectRegistry.json` if available during development.

---

## 5. Transaction Lifecycle & Confirmation

When `BlockchainService.register_project_version()` is called:
1. **Validation**:
   - `registration_id`: non-empty format validation.
   - `composite_hash`: validates 64 hex characters and rejects zero hash (`0x00...00`). Converted to `bytes32`.
   - `ipfs_root_cid`: non-empty string validation.
   - `version_index`: validated $\ge 1$.
   - `lifecycle_stage`: translated to Solidity enum integer (`IDEA=0, DESIGN=1, PROTOTYPE=2, FINAL=3`).
   - `author` & `co_authors`: normalized to EIP-55 checksum addresses.
2. **Chain ID Verification**: Compares active network chain ID with configured `BLOCKCHAIN_CHAIN_ID` to prevent accidental broadcast to wrong networks.
3. **Nonce Management**: Fetches pending transaction count for relayer address.
4. **Gas Estimation**:
   - Simulates function execution on node via `estimate_gas()`.
   - Adds 20% safety margin.
   - Supports EIP-1559 dynamic fee calculation with priority fee fallback.
5. **Signing & Broadcast**: Signs raw transaction with `eth_account.Account.sign_transaction` and broadcasts via `w3.eth.send_raw_transaction`.
6. **Receipt Confirmation**:
   - Awaits receipt up to `BLOCKCHAIN_TIMEOUT_SECONDS`.
   - Verifies `receipt.status == 1`.
   - Checks confirmation depth: `current_height - receipt.blockNumber + 1 >= confirmation_blocks`.
7. **Timestamping & Event Extraction**:
   - Queries block timestamp from `w3.eth.get_block(receipt.blockNumber)`.
   - Decodes `ProjectVersionRegistered` event logs to obtain canonical `recordId`.

---

## 6. Public Trustless Verification

The `verify_project_version(registration_id, expected_hash)` method invokes the `view` function `ProjectRegistry.verifyProjectVersion()`:
- **Missing Registrations**: Returns `is_valid: False` with `0` timestamp and null values without reverting.
- **Hash Mismatches**: Returns `is_valid: False` with the on-chain timestamp, IPFS CID, and author, allowing verifiers to distinguish between "not found" and "tampered content".
- **Matching Proofs**: Returns `is_valid: True` with full on-chain timestamp, IPFS root CID, author wallet, and active dispute state.

---

## 7. Error Handling Architecture

All blockchain, Web3, RPC, and contract errors are normalized into `BlockchainException(AppException)`:

| Error Code | HTTP Status | Trigger Condition |
|---|---|---|
| `BLOCKCHAIN_NOT_CONFIGURED` | 502 | `PROJECT_REGISTRY_CONTRACT_ADDRESS` is empty |
| `BLOCKCHAIN_CONFIGURATION_ERROR` | 502 | Invalid private key or relayer uninitialized |
| `BLOCKCHAIN_CONNECTION_ERROR` | 502 | RPC endpoint unresponsive / timeout |
| `BLOCKCHAIN_CHAIN_ID_MISMATCH` | 502 | Connected network does not match expected chain ID |
| `BLOCKCHAIN_INVALID_HASH` | 422 | Non-64 character hex or zero hash |
| `BLOCKCHAIN_INVALID_ADDRESS` | 422 | Invalid Ethereum address formatting |
| `BLOCKCHAIN_TRANSACTION_FAILED` | 502 | Contract simulation reverted or mined with status 0 |
| `BLOCKCHAIN_TRANSACTION_TIMEOUT` | 502 | Transaction receipt not mined within timeout |
| `BLOCKCHAIN_INSUFFICIENT_FUNDS` | 502 | Relayer account has insufficient ETH for gas |
| `VERSION_NOT_FOUND` | 404 | Raised during `get_project_version()` if record missing |

---

## 8. Testing Strategy

### Unit Tests (Isolated Mocking)
Located in `backend/tests/test_blockchain_service.py`. Covers all 32 core scenarios using mocked Web3 calls without requiring a live node:
- Service initialization and configuration rejection
- Checksum and hash conversions
- Lifecycle enum conversions
- Nonce and transaction signing mechanics
- Transaction revert and timeout handling
- Event log decoding
- Sensitive key masking in exceptions

Run unit tests:
```powershell
& "backend\.venv\Scripts\pytest.exe" -v backend/tests/test_blockchain_service.py
```

### Live Integration Verification
Located in `backend/scripts/verify_web3_live.py`. Performs end-to-end testing against an active local Hardhat node:
1. Start local Hardhat node:
   ```powershell
   cd blockchain
   npx hardhat node
   ```
2. In a separate terminal, execute verification:
   ```powershell
   & "backend\.venv\Scripts\python.exe" backend/scripts/verify_web3_live.py
   ```
The script will deploy a temporary `ProjectRegistry`, register a version, query the proof, verify the hash, raise a dispute, and resolve the dispute.
