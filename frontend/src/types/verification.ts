// Verification domain types matching API_CONTRACT.md Module 6 & FRONTEND_BACKEND_CONTRACT.md

import { DisputeStatus, LifecycleStage } from './project';

export interface BlockchainProof {
  transaction_hash: string;
  block_number: number;
  block_timestamp: string;
  smart_contract_address: string;
  author_wallet: string;
  network_name?: string;
  dispute_status: DisputeStatus;
  match_confirmed: boolean;
}

export interface VerificationProjectSummary {
  public_id: string;
  title: string;
  department: string;
  institution_name?: string | null;
}

export interface VerificationVersionSummary {
  version_tag: string;
  lifecycle_stage: LifecycleStage;
  composite_sha256: string;
  ipfs_root_cid: string;
}

export interface VerificationResponseData {
  is_valid: boolean;
  registration_id: string;
  project: VerificationProjectSummary;
  version: VerificationVersionSummary;
  blockchain_proof: BlockchainProof;
}

export interface VerifyHashRequest {
  sha256_hash: string;
  registration_id?: string;
}
