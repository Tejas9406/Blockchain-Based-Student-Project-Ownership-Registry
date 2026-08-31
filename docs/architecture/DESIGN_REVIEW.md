# System Contract Consistency & Final Architecture Review

> **Project**: Blockchain-Based Student Project Ownership Registry (CYB05)  
> **Phase**: Phase 1 — System Contract Final Architecture Review  
> **Reviewer**: Senior Software Architect  
> **Date**: 2026-08-31  
> **Document Version**: 2.0 (Post-Clarification Pass)  
> **Final Verdict**: **GREEN — READY FOR PARALLEL DEVELOPMENT**

---

## 1. Executive Summary

A thorough architectural clarification pass was conducted across all frozen Phase 1 system contract documents:
1. [`docs/database/DATABASE_DESIGN.md`](file:///e:/SIH-Blockchain-Project/Blockchain-Based-Student-Project-Ownership-Registry/docs/database/DATABASE_DESIGN.md)
2. [`docs/api/API_CONTRACT.md`](file:///e:/SIH-Blockchain-Project/Blockchain-Based-Student-Project-Ownership-Registry/docs/api/API_CONTRACT.md)
3. [`docs/blockchain/BLOCKCHAIN_DESIGN.md`](file:///e:/SIH-Blockchain-Project/Blockchain-Based-Student-Project-Ownership-Registry/docs/blockchain/BLOCKCHAIN_DESIGN.md)
4. [`docs/api/FRONTEND_BACKEND_CONTRACT.md`](file:///e:/SIH-Blockchain-Project/Blockchain-Based-Student-Project-Ownership-Registry/docs/api/FRONTEND_BACKEND_CONTRACT.md)
5. [`docs/architecture/INTEGRATION_CONTRACT.md`](file:///e:/SIH-Blockchain-Project/Blockchain-Based-Student-Project-Ownership-Registry/docs/architecture/INTEGRATION_CONTRACT.md)

All domain contracts, data models, state machines, and cryptographic algorithms are synchronized and frozen.

---

## 2. Comprehensive Architectural Audit Matrix

| # | Architecture Review Item | Status | Verification & Rationale |
| :-: | :--- | :---: | :--- |
| **1** | **Deterministic Composite SHA-256 Algorithm** | **PASS** | Formally specified in `BLOCKCHAIN_DESIGN.md` with participating fields (`file_name:file_size_bytes:sha256_hash`), ASCII lexicographical sorting, UTF-8 encoding, Unix `\n` delimiters, and a complete worked example producing a concrete `bytes32` digest. |
| **2** | **Relayer vs. Project Owner & Trust Boundary** | **PASS** | Explicit separation documented: `msg.sender` represents the platform Gas Relayer, while `author` and `coAuthors` represent the authenticated student wallets recorded explicitly in the smart contract's `VersionProof` record. |
| **3** | **Idempotency Strategy** | **PASS** | Multi-layer deduplication specified: client `Idempotency-Key` header, database constraints `UNIQUE(project_id, version_index)` and `UNIQUE(registration_id)`, with safe retry interception returning cached records without duplicate transactions. |
| **4** | **Version Status State Machine** | **PASS** | Defined states: `DRAFT`, `PENDING`, `ANCHORING`, `ANCHORED`, `FAILED`. Mermaid state transition diagram in `DATABASE_DESIGN.md` explicitly enforces legal paths and disallows arbitrary state mutations. |
| **5** | **Separation of Registration & Dispute Lifecycles** | **PASS** | `anchoring_status` (`DRAFT`..`ANCHORED`) and `dispute_status` (`NONE`, `OPEN`, `UNDER_REVIEW`, `RESOLVED`, `REJECTED`) are modeled as separate attributes with distinct state machines in both PostgreSQL and Solidity. |
| **6** | **Exhaustive Failure Scenarios Matrix** | **PASS** | Detailed recovery matrix in `INTEGRATION_CONTRACT.md` covers Scenarios A–F (IPFS failure, Blockchain failure, Backend timeout, DB sync failure, User retry, and Hash mismatch detection). |
| **7** | **QR Code Design (MVP vs. Future)** | **PASS** | MVP explicitly defines QR as encoding the public verification URL (`https://registry.sih2026.edu/verify/REG-YYYY-XXXXX`). Cryptographically signed W3C credentials marked as **FUTURE ENHANCEMENT**. |
| **8** | **AI Similarity Scoping** | **PASS** | Explicitly classified as **FUTURE ENHANCEMENT**. MVP project registration, SHA-256 hashing, IPFS pinning, and blockchain verification operate independently without AI service dependencies. |
| **9** | **Authoritative Data Model Mapping** | **PASS** | Comprehensive table mapping authoritative proof (Blockchain/IPFS) vs. application index/metadata (PostgreSQL) documented in `DATABASE_DESIGN.md` and `BLOCKCHAIN_DESIGN.md`. |
| **10**| **Dispute Filing Window Policy** | **OPEN DECISION** | Removed fixed 14-day technical constraint. Documented as an institutional product/policy decision that does not block core smart contract or API development. |
| **11**| **Cross-Module Type & Terminology Consistency** | **PASS** | Unified nomenclature (`composite_sha256`, `ipfs_root_cid`, `registration_id`, `anchoring_status`, `dispute_status`) and ISO 8601 UTC timestamp formats verified across all 5 contract documents. |

---

## 3. Final Architecture Decision

# `GREEN — READY FOR PARALLEL DEVELOPMENT`

### Criteria Verification:
* [x] Composite hashing is deterministic with complete worked example.
* [x] Relayer / Owner distinction and trust boundary are clearly defined.
* [x] Idempotency and retry semantics are fully specified.
* [x] Failure states and recovery flows are mapped across all layers.
* [x] Dispute lifecycle is separated from registration status.
* [x] QR code design is established as a clean verification URL for MVP.
* [x] AI similarity detection is isolated as a post-MVP future enhancement.
* [x] All 5 system contract documents are 100% consistent with zero code implementations touched.

**The architecture is frozen. Parallel development for Phase 2 can now commence.**
