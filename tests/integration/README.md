# Integration & End-to-End Testing Suite

> **Project**: Blockchain-Based Student Project Ownership Registry (CYB05)  
> **Scope**: Cross-Module Integration Tests (React Frontend ↔ FastAPI Backend ↔ PostgreSQL ↔ IPFS ↔ Blockchain)  
> **Status**: **PLACEHOLDER FOUNDATION — INTEGRATION TESTS WILL BE BUILT IN PHASE 3/4**

---

## 1. Planned Integration Scenarios

1. **Full Registration & Anchoring Flow**:
   - Client uploads project files.
   - Backend computes SHA-256 and pins artifact to IPFS.
   - Backend calls smart contract to anchor `bytes32` digest.
   - Database stores version record with transaction receipt.
   - Verification endpoint successfully validates matching file against on-chain hash.

2. **Tamper Detection Test**:
   - File is modified by 1 byte.
   - Verification endpoint detects hash divergence and rejects proof.

3. **Version Provenance Audit Trail**:
   - Submitting v1, v2, v3 creates sequential on-chain provenance records linked to original project ID.

4. **Multi-User Permission Guardrails**:
   - Non-members cannot update project metadata or submit new versions.

---

## 2. Directory Layout (Planned)

```
tests/integration/
├── test_e2e_registration.py       # Full student submission to on-chain proof
├── test_e2e_verification.py         # Third-party hash/file verification
├── test_tamper_detection.py        # Cryptographic mismatch validation
├── test_dispute_workflow.py        # Timestamp conflict resolution
└── conftest.py                     # Shared multi-service fixtures
```
