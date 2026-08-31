# REST API Contract Specification (v1)

> **Project**: Blockchain-Based Student Project Ownership Registry (CYB05)  
> **API Version**: `/api/v1`  
> **Protocol**: HTTP/1.1 over TLS (HTTPS)  
> **Document Version**: 3.0 (Phase 1 — Final Frozen Architecture)  
> **Audience**: Developer 1 (Frontend Lead), Developer 2 (Backend Lead), Developer 3 (Blockchain Lead)

---

## 1. Global Conventions & Standards

### 1.1 API Prefix & Base URL
* **Development Local**: `http://localhost:8000/api/v1`
* **Production Gateway**: `https://registry.sih2026.edu/api/v1`

### 1.2 Authentication & Idempotency Headers
All protected requests must include the standard OAuth2 Bearer token:
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```
Mutating POST requests (such as creating a version) accept an optional client idempotency key:
```http
Idempotency-Key: 9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d
```

### 1.3 Role-Based Access Control (RBAC)
| Role Name | Description & Permissions |
| :--- | :--- |
| **`PUBLIC`** | Unauthenticated user; can view public projects, verify hashes, inspect certificates, and query QR verification URLs. |
| **`STUDENT`** | Authenticated student; can register projects, invite team members, upload artifacts, create milestones, and raise disputes. |
| **`FACULTY`** | Authenticated faculty mentor; can review mentored projects, endorse milestones, and co-sign submissions. |
| **`VERIFIER`** | Institutional evaluator, patent agent, or hackathon jury; can access high-volume verification endpoints. |
| **`ADMIN`** | Institutional / platform administrator; can adjudicate disputes, manage user accounts, and view global audit logs. |

---

## 2. Feature Scoping & Roadmap Boundaries

### 2.1 Core MVP Capabilities (Phase 1 & Phase 2 Scope)
1. User Registration & Authentication (Argon2id + JWT).
2. Project Creation & Team Member Management.
3. Multi-file Artifact Ingestion & Deterministic Composite SHA-256 Hashing.
4. IPFS Decentralized Directory DAG Pinning.
5. On-Chain Cryptographic Proof Anchoring (`ProjectRegistry.sol`).
6. Trustless Public Verification Portal (by Registration ID, Hash, or File Upload).
7. PDF Ownership Certificates & Static URL-Encoded QR Codes.
8. Basic Plagiarism / Ownership Dispute Filing & Admin Adjudication.

### 2.2 Future Enhancements (Post-MVP Scope)
* **AI Similarity & Plagiarism Engine**: Automated embedding comparisons, semantic code similarity, and prior-art NLP matching.
* **Cryptographically Signed QR Codes**: Embedded W3C Verifiable Credentials with Ed25519 institutional digital signatures.
* **Decentralized Dispute Governance**: Token-weighted or faculty jury decentralized dispute voting.

---

## 3. Universal Response Envelope Standards

### 3.1 Standard Success Envelope
```json
{
  "success": true,
  "data": {},
  "meta": {
    "timestamp": "2026-08-31T18:50:00.000Z",
    "request_id": "req-8f29a-11e2"
  }
}
```

### 3.2 Standard Paginated Success Envelope
```json
{
  "success": true,
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 142,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false,
    "timestamp": "2026-08-31T18:50:00.000Z"
  }
}
```

### 3.3 Universal Error Response Envelope
```json
{
  "success": false,
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "The requested project identifier does not exist.",
    "details": {
      "field": "project_id",
      "value": "PRJ-202608-00000"
    }
  },
  "meta": {
    "timestamp": "2026-08-31T18:50:00.000Z",
    "request_id": "req-8f29a-11e2"
  }
}
```

---

## 4. Module 1: Authentication Endpoints (`/api/v1/auth`)

### 4.1 Register User
* **Method**: `POST`
* **URL**: `/api/v1/auth/register`
* **Auth Requirement**: `PUBLIC`
* **Success Response** (`201 Created`): Returns created user public profile.

### 4.2 User Login
* **Method**: `POST`
* **URL**: `/api/v1/auth/login`
* **Auth Requirement**: `PUBLIC`
* **Success Response** (`200 OK`): Returns `access_token`, `refresh_token`, and user summary.

### 4.3 Refresh Access Token
* **Method**: `POST`
* **URL**: `/api/v1/auth/refresh`
* **Auth Requirement**: `PUBLIC`

### 4.4 Get Current User Profile
* **Method**: `GET`
* **URL**: `/api/v1/auth/me`
* **Auth Requirement**: `Bearer JWT`

---

## 5. Module 2: Project Management Endpoints (`/api/v1/projects`)

### 5.1 Create New Project
* **Method**: `POST`
* **URL**: `/api/v1/projects`
* **Auth Requirement**: `Bearer JWT` (`STUDENT`, `FACULTY`)

### 5.2 List Projects
* **Method**: `GET`
* **URL**: `/api/v1/projects`
* **Auth Requirement**: `PUBLIC`
* **Query Parameters**: `page`, `page_size`, `category`, `department`, `lifecycle_stage`, `search`.

### 5.3 Get Project Details by ID or Slug
* **Method**: `GET`
* **URL**: `/api/v1/projects/{project_identifier}`
* **Auth Requirement**: `PUBLIC` (or Authenticated for private projects)

---

## 6. Module 3: Project Members & Team (`/api/v1/projects/{id}/members`)

### 6.1 List Members
* **Method**: `GET`
* **URL**: `/api/v1/projects/{project_id}/members`
* **Auth Requirement**: `PUBLIC`

### 6.2 Add / Invite Team Member
* **Method**: `POST`
* **URL**: `/api/v1/projects/{project_id}/members`
* **Auth Requirement**: `Bearer JWT` (Project Owner Only)

---

## 7. Module 4: Version & Milestone Anchoring (`/api/v1/projects/{id}/versions`)

### 7.1 Create Project Version Snapshot & Anchor on Blockchain
* **Method**: `POST`
* **URL**: `/api/v1/projects/{project_id}/versions`
* **Headers**: `Idempotency-Key` (Optional UUID)
* **Auth Requirement**: `Bearer JWT` (Project Lead/Owner)
* **Request Body**:
```json
{
  "version_tag": "v1.0",
  "lifecycle_stage": "DESIGN",
  "title": "System Architecture & Threat Model",
  "description": "Initial architectural specifications, data flow diagrams, and threat model analysis.",
  "artifact_ids": [
    "ART-202608-11E54",
    "ART-202608-11E55"
  ]
}
```
* **Success Response** (`202 Accepted` / `201 Created`):
```json
{
  "success": true,
  "data": {
    "public_id": "VER-202608-41C88",
    "registration_id": "REG-2026-A8F92D",
    "version_index": 1,
    "version_tag": "v1.0",
    "lifecycle_stage": "DESIGN",
    "title": "System Architecture & Threat Model",
    "composite_sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    "ipfs_root_cid": "bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m",
    "anchoring_status": "ANCHORING",
    "dispute_status": "NONE",
    "blockchain_record": {
      "transaction_hash": "0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb",
      "network_name": "sepolia"
    }
  }
}
```

---

## 8. Module 5: Artifact Ingestion (`/api/v1/artifacts`)

### 8.1 Upload Artifact File
* **Method**: `POST`
* **URL**: `/api/v1/artifacts/upload`
* **Auth Requirement**: `Bearer JWT` (`STUDENT`, `FACULTY`)
* **Content-Type**: `multipart/form-data`
* **Form Parameters**: `file` (max 50 MB), `artifact_category`

---

## 9. Module 6: Verification Engine (`/api/v1/verification`)

### 9.1 Verify by Registration ID
* **Method**: `GET`
* **URL**: `/api/v1/verification/verify-registration/{registration_id}`
* **Auth Requirement**: `PUBLIC`
* **Success Response** (`200 OK`):
```json
{
  "success": true,
  "data": {
    "is_valid": true,
    "registration_id": "REG-2026-A8F92D",
    "project": {
      "public_id": "PRJ-202608-99B12",
      "title": "Decentralized IPFS Academic Registry",
      "department": "Computer Science & Engineering",
      "institution_name": "National Institute of Technology"
    },
    "version": {
      "version_tag": "v1.0",
      "lifecycle_stage": "DESIGN",
      "composite_sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
      "ipfs_root_cid": "bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m"
    },
    "blockchain_proof": {
      "transaction_hash": "0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb",
      "block_number": 142981,
      "block_timestamp": "2026-08-31T18:50:00.000Z",
      "smart_contract_address": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
      "author_wallet": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
      "dispute_status": "NONE",
      "match_confirmed": true
    }
  }
}
```

### 9.2 Verify Raw SHA-256 Hash
* **Method**: `POST`
* **URL**: `/api/v1/verification/verify-hash`
* **Auth Requirement**: `PUBLIC`

### 9.3 Verify Uploaded File Directly
* **Method**: `POST`
* **URL**: `/api/v1/verification/verify-file`
* **Auth Requirement**: `PUBLIC`

---

## 10. Module 7: Certificates & QR Verification Codes (`/api/v1/certificates`)

### 10.1 Get Certificate Metadata
* **Method**: `GET`
* **URL**: `/api/v1/certificates/{registration_id}`
* **Auth Requirement**: `PUBLIC`
* **Success Response** (`200 OK`):
```json
{
  "success": true,
  "data": {
    "registration_id": "REG-2026-A8F92D",
    "project_title": "Decentralized IPFS Academic Registry",
    "version_tag": "v1.0",
    "authors": ["Tejas Sharma", "Aman Verma"],
    "institution": "National Institute of Technology",
    "anchored_timestamp": "2026-08-31T18:50:00.000Z",
    "transaction_hash": "0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb",
    "verification_url": "https://registry.sih2026.edu/verify/REG-2026-A8F92D",
    "qr_code_svg_url": "https://registry.sih2026.edu/api/v1/certificates/REG-2026-A8F92D/qr.svg",
    "pdf_download_url": "https://registry.sih2026.edu/api/v1/certificates/REG-2026-A8F92D/download"
  }
}
```

### 10.2 Get QR Code (URL-Encoded Payload)
* **Method**: `GET`
* **URL**: `/api/v1/certificates/{registration_id}/qr`
* **Auth Requirement**: `PUBLIC`
* **Description**: Returns standard QR code encoding the direct public verification URL (`https://registry.sih2026.edu/verify/REG-YYYY-XXXXX`).

---

## 11. Module 8: Disputes (`/api/v1/disputes`)

### 11.1 Raise Ownership Dispute
* **Method**: `POST`
* **URL**: `/api/v1/disputes`
* **Auth Requirement**: `Bearer JWT` (`STUDENT`, `FACULTY`)
* **Success Response** (`201 Created`): Creates dispute record with status `OPEN`.

---

## 12. Module 9: Admin Management (`/api/v1/admin`)

### 12.1 Adjudicate Dispute
* **Method**: `PATCH`
* **URL**: `/api/v1/admin/disputes/{dispute_id}/adjudicate`
* **Auth Requirement**: `Bearer JWT` (`ADMIN` Role Only)
* **Request Body**:
```json
{
  "resolution_status": "REJECTED",
  "resolution_notes": "Claimant failed to demonstrate prior art; on-chain timestamp confirms respondent precedence."
}
```
