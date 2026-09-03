// Artifact domain types matching API_CONTRACT.md Module 5 & FRONTEND_BACKEND_CONTRACT.md

export type ArtifactCategory = 
  | 'SOURCE_CODE' 
  | 'DOCUMENTATION' 
  | 'DESIGN_SPEC' 
  | 'PRESENTATION' 
  | 'OTHER';

export interface ArtifactItem {
  public_id: string;          // "ART-202608-11E54"
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  ipfs_cid: string;
  artifact_category: ArtifactCategory;
  uploaded_at: string;
}

export interface ArtifactResponse {
  public_id: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  ipfs_cid: string;
  artifact_category: ArtifactCategory;
  uploaded_at: string;
}
