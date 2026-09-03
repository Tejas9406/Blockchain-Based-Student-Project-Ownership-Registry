// Certificate domain types matching API_CONTRACT.md Module 7 & FRONTEND_BACKEND_CONTRACT.md

export interface CertificateMetadataData {
  registration_id: string;    // "REG-2026-A8F92D"
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
