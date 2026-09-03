// Dispute domain types matching API_CONTRACT.md Module 8 & 9 and FRONTEND_BACKEND_CONTRACT.md

import { DisputeStatus } from './project';

export type DisputeType = 'PLAGIARISM' | 'UNAUTHORIZED_USE' | 'CITATION_FAILURE' | 'OTHER';

export interface DisputeClaimantSummary {
  public_id: string;
  full_name: string;
  institution_id?: string | null;
}

export interface DisputeDetailResponse {
  public_id: string;
  project_public_id: string;
  project_title: string;
  registration_id?: string | null;
  dispute_type: DisputeType | string;
  claim_description: string;
  evidence_url?: string | null;
  status: DisputeStatus | string;
  resolution_notes?: string | null;
  transaction_hash?: string | null;
  resolution_transaction_hash?: string | null;
  claimant?: DisputeClaimantSummary | null;
  created_at: string;
  resolved_at?: string | null;
}

export type Dispute = DisputeDetailResponse;

export interface DisputeCreateRequest {
  project_id?: string;
  registration_id?: string;
  dispute_type: DisputeType | string;
  claim_description: string;
  evidence_url?: string;
}

export interface DisputeAdjudicateRequest {
  resolution_status: 'RESOLVED' | 'REJECTED';
  resolution_notes: string;
}
