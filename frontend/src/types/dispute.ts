// Dispute domain types matching API_CONTRACT.md Module 8 & 9 and FRONTEND_BACKEND_CONTRACT.md

import { DisputeStatus } from './project';

export type DisputeType = 'PLAGIARISM' | 'UNAUTHORIZED_USE' | 'CITATION_FAILURE' | 'OTHER';

export interface DisputeDetailResponse {
  public_id: string;          // "DSP-202608-XXXXX"
  project_id: string;
  claimant_user_id: string;
  dispute_type: DisputeType;
  claim_description: string;
  evidence_url?: string | null;
  status: DisputeStatus;
  resolution_notes?: string | null;
  resolved_by_admin_id?: string | null;
  created_at: string;
  resolved_at?: string | null;
}

export interface DisputeCreateRequest {
  project_id: string;
  dispute_type: DisputeType;
  claim_description: string;
  evidence_url?: string;
}

export interface DisputeAdjudicateRequest {
  resolution_status: 'RESOLVED' | 'REJECTED';
  resolution_notes: string;
}
