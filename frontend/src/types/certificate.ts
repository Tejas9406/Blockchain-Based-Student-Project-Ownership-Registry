// Certificate domain types matching API_CONTRACT.md Module 7 & FRONTEND_BACKEND_CONTRACT.md

export interface CertificateMetadataData {
  registration_id: string;    // "REG-2026-A8F92D"
  project_title: string;
  version_tag: string;
  lifecycle_stage?: string | null;
  authors: string[];
  institution?: string | null;
  department?: string | null;
  anchored_timestamp?: string | null;
  transaction_hash: string;
  block_number?: number | null;
  composite_sha256?: string | null;
  ipfs_root_cid?: string | null;
  verification_url: string;   // "https://registry.sih2026.edu/verify/REG-2026-A8F92D"
  qr_code_svg_url: string;
  pdf_download_url: string;
  dispute_status: string;     // "NONE" | "REJECTED" | "OPEN" | "UNDER_REVIEW" | "RESOLVED"
}

export type Certificate = CertificateMetadataData;

export interface CertificateMetadataResponse {
  success: boolean;
  data: CertificateMetadataData;
  meta?: {
    timestamp: string;
  };
}
