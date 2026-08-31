# Frontend ↔ Backend Integration Contract

> **Project**: Blockchain-Based Student Project Ownership Registry (CYB05)  
> **Target Frontend**: React 18 + Vite + TypeScript + Tailwind CSS + Axios  
> **Target Backend**: FastAPI + Pydantic v2 + Python 3.13  
> **Document Version**: 3.0 (Phase 1 — Final Frozen Architecture)  
> **Audience**: Developer 1 (Frontend Lead), Developer 2 (Backend Lead)

---

## 1. Purpose & Design Principles

This document establishes the **strict runtime communication contract** between the React Single Page Application (Developer 1) and the FastAPI Backend (Developer 2). 

By freezing these standards, Developer 1 can build complete UI views, mock service layers, state stores, and form validations without depending on live backend implementation.

---

## 2. Global Communication Standards

### 2.1 Base URLs & Environment Variables
The frontend accesses the backend via `VITE_API_BASE_URL`:
```typescript
// frontend/src/services/api.ts
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
```

| Environment | Base API URL |
| :--- | :--- |
| **Local Development** | `http://localhost:8000/api/v1` |
| **Docker Compose** | `http://localhost:8000/api/v1` (browser host perspective) |
| **Production Staging** | `https://api.staging.registry.sih2026.edu/api/v1` |

### 2.2 Property Naming & Case Convention
* **All JSON request and response payloads use `snake_case`**.
* The frontend TypeScript interfaces strictly mirror these `snake_case` keys to eliminate serialization bugs.

### 2.3 Date and Time Serialization
* All timestamps are returned as **ISO 8601 Strings in UTC timezone**:
  * Format: `YYYY-MM-DDTHH:mm:ss.sssZ`
  * Example: `"2026-08-31T18:50:00.000Z"`
* Frontend parses timestamps using standard `new Date(isoString)` or formatting libraries.

### 2.4 Authentication & Idempotency Headers
For protected endpoints, the frontend Axios interceptor automatically attaches the stored JWT:
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```
For milestone/version submissions, the frontend attaches a unique UUID `Idempotency-Key` header:
```http
Idempotency-Key: 9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d
```

---

## 3. Universal Response Envelopes & TypeScript Definitions

### 3.1 TypeScript Standard Envelopes

```typescript
// Global API Meta Structure
export interface ApiMeta {
  timestamp: string;
  request_id?: string;
}

// Paginated Meta Structure
export interface PaginatedMeta extends ApiMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// Universal Success Envelope
export interface ApiResponse<T> {
  success: true;
  data: T;
  meta: ApiMeta;
}

// Universal Paginated Response Envelope
export interface ApiPaginatedResponse<T> {
  success: true;
  data: T[];
  meta: PaginatedMeta;
}

// Universal Error Detail
export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// Universal Error Envelope
export interface ApiErrorResponse {
  success: false;
  error: ApiErrorDetail;
  meta: ApiMeta;
}
```

---

## 4. Core Domain TypeScript Models

```typescript
export type UserRole = 'STUDENT' | 'FACULTY' | 'ADMIN' | 'VERIFIER';
export type LifecycleStage = 'IDEA' | 'DESIGN' | 'PROTOTYPE' | 'FINAL';
export type ProjectStatus = 'ACTIVE' | 'ARCHIVED' | 'UNDER_DISPUTE';
export type MemberRole = 'LEAD' | 'CONTRIBUTOR' | 'FACULTY_MENTOR';
export type AnchoringStatus = 'DRAFT' | 'PENDING' | 'ANCHORING' | 'ANCHORED' | 'FAILED';
export type DisputeStatus = 'NONE' | 'OPEN' | 'UNDER_REVIEW' | 'RESOLVED' | 'REJECTED';

export interface UserProfile {
  public_id: string;          // "USR-202608-8F29A"
  email: string;
  full_name: string;
  institution_id: string;
  institution_name: string;
  department: string;
  role: UserRole;
  wallet_address?: string;
  is_verified: boolean;
  created_at: string;
}

export interface ProjectSummary {
  public_id: string;          // "PRJ-202608-99B12"
  slug: string;               // "decentralized-ipfs-academic-registry"
  title: string;
  abstract: string;
  category: string;
  department: string;
  academic_year: string;
  current_lifecycle_stage: LifecycleStage;
  visibility: 'PUBLIC' | 'INSTITUTIONAL' | 'PRIVATE';
  status: ProjectStatus;
  owner: {
    public_id: string;
    full_name: string;
  };
  created_at: string;
}

export interface ProjectMemberItem {
  user: UserProfile;
  role_in_project: MemberRole;
  contribution_percentage: number;
  is_owner: boolean;
  joined_at: string;
}

export interface ArtifactItem {
  public_id: string;          // "ART-202608-11E54"
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  ipfs_cid: string;
  artifact_category: string;
  uploaded_at: string;
}

export interface BlockchainProof {
  transaction_hash: string;
  block_number: number;
  anchored_timestamp: string;
  smart_contract_address: string;
  author_wallet: string;
  network_name: string;
  dispute_status?: DisputeStatus;
  match_confirmed?: boolean;
}

export interface VersionDetail {
  public_id: string;          // "VER-202608-41C88"
  registration_id: string;    // "REG-2026-A8F92D"
  version_index: number;
  version_tag: string;        // "v1.0"
  lifecycle_stage: LifecycleStage;
  title: string;
  description: string;
  composite_sha256: string;
  ipfs_root_cid: string;
  anchoring_status: AnchoringStatus;
  dispute_status: DisputeStatus;
  artifacts?: ArtifactItem[];
  blockchain_record?: BlockchainProof;
  created_at: string;
}

export interface VerificationResult {
  is_valid: boolean;
  registration_id: string;
  project: {
    public_id: string;
    title: string;
    department: string;
    institution_name: string;
  };
  version: {
    version_tag: string;
    lifecycle_stage: LifecycleStage;
    composite_sha256: string;
    ipfs_root_cid: string;
  };
  blockchain_proof: BlockchainProof;
}

export interface CertificateMetadata {
  registration_id: string;
  project_title: string;
  version_tag: string;
  authors: string[];
  institution: string;
  anchored_timestamp: string;
  transaction_hash: string;
  verification_url: string;   // "https://registry.sih2026.edu/verify/REG-2026-A8F92D"
  qr_code_svg_url: string;
  pdf_download_url: string;
}
```

---

## 5. File Upload & Multipart Form Convention

### 5.1 Artifact Upload Workflow
* **Endpoint**: `POST /api/v1/artifacts/upload`
* **Headers**: `Content-Type: multipart/form-data`
* **Form Payload**:
  * `file`: File Object (Browser File API)
  * `artifact_category`: `"SOURCE_CODE"` | `"DOCUMENTATION"` | `"DESIGN_SPEC"` | `"PRESENTATION"` | `"OTHER"`
* **Size Limit**: Single file maximum: **50 MB**.
* **Accepted Formats**: `.pdf`, `.zip`, `.tar.gz`, `.ipynb`, `.docx`, `.png`, `.jpg`, `.stl`, `.json`.

---

## 6. Frontend Error Handling Pattern & Idempotent Submission

```typescript
import axios from 'axios';
import { apiClient } from './api';
import { ApiResponse, ApiErrorResponse, VersionDetail } from './types';

export async function submitProjectVersion(
  projectId: string, 
  payload: { version_tag: string; lifecycle_stage: string; title: string; description: string; artifact_ids: string[] },
  idempotencyKey: string
): Promise<VersionDetail> {
  try {
    const response = await apiClient.post<ApiResponse<VersionDetail>>(
      `/projects/${projectId}/versions`,
      payload,
      {
        headers: {
          'Idempotency-Key': idempotencyKey,
        },
      }
    );
    return response.data.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      const errPayload = error.response.data as ApiErrorResponse;
      throw new Error(errPayload.error.message || 'Failed to anchor project version.');
    }
    throw new Error('Network error: Unable to connect to registry backend.');
  }
}
```
