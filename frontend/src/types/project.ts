// Project & Version domain types matching API_CONTRACT.md Modules 2, 3, 4 & FRONTEND_BACKEND_CONTRACT.md

import { UserRole } from './auth';

export type LifecycleStage = 'IDEA' | 'DESIGN' | 'PROTOTYPE' | 'FINAL';
export type ProjectStatus = 'ACTIVE' | 'ARCHIVED' | 'UNDER_DISPUTE';
export type MemberRole = 'LEAD' | 'CONTRIBUTOR' | 'FACULTY_MENTOR';
export type AnchoringStatus = 'DRAFT' | 'PENDING' | 'ANCHORING' | 'ANCHORED' | 'FAILED';
export type DisputeStatus = 'NONE' | 'OPEN' | 'UNDER_REVIEW' | 'RESOLVED' | 'REJECTED';

export interface ProjectSummary {
  public_id: string;          // "PRJ-202608-99B12"
  slug: string;               // "decentralized-ipfs-academic-registry"
  title: string;
  abstract?: string | null;
  category: string;
  department: string;
  academic_year: string;
  current_lifecycle_stage: LifecycleStage;
  visibility: 'PUBLIC' | 'INSTITUTIONAL' | 'PRIVATE';
  status: ProjectStatus;
  owner?: {
    public_id: string;
    full_name: string;
  };
  created_at: string;
  updated_at?: string;
}

export interface ProjectCreateRequest {
  title: string;
  abstract?: string | null;
  category: string;
  department: string;
  academic_year: string;
  visibility?: 'PUBLIC' | 'INSTITUTIONAL' | 'PRIVATE';
}

export interface ProjectMemberItem {
  user: {
    public_id: string;
    email: string;
    full_name: string;
    role: UserRole;
    department?: string | null;
  };
  role_in_project: MemberRole;
  contribution_percentage: number;
  is_owner: boolean;
  joined_at: string;
}

export interface ProjectMemberCreateRequest {
  user_email_or_id: string;
  role_in_project: MemberRole;
  contribution_percentage?: number;
}

export interface ArtifactReference {
  public_id: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  ipfs_cid: string;
  artifact_category: string;
  uploaded_at: string;
}

export interface BlockchainRecordSummary {
  transaction_hash: string;
  block_number?: number;
  anchored_timestamp?: string;
  smart_contract_address?: string;
  author_wallet?: string;
  network_name?: string;
}

export interface ProjectVersionDetail {
  public_id: string;          // "VER-202608-41C88"
  registration_id: string;    // "REG-2026-A8F92D"
  version_index: number;
  version_tag: string;        // "v1.0"
  lifecycle_stage: LifecycleStage;
  title: string;
  description?: string | null;
  composite_sha256: string;
  ipfs_root_cid: string;
  anchoring_status: AnchoringStatus;
  dispute_status: DisputeStatus;
  artifacts?: ArtifactReference[];
  blockchain_record?: BlockchainRecordSummary | null;
  created_at: string;
}

export interface ProjectVersionCreateRequest {
  version_tag: string;
  lifecycle_stage: LifecycleStage;
  title: string;
  description?: string;
  artifact_ids: string[];
}
