// Global API Envelopes & Error Structures matching frozen API_CONTRACT.md & FRONTEND_BACKEND_CONTRACT.md

export interface ApiMeta {
  timestamp: string;
  request_id?: string;
}

export interface PaginatedMeta extends ApiMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ApiResponse<T> {
  success: true;
  data: T;
  meta: ApiMeta;
}

export interface ApiPaginatedResponse<T> {
  success: true;
  data: T[];
  meta: PaginatedMeta;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, any>;
}

export interface ApiErrorResponse {
  success: false;
  error: ApiErrorDetail;
  meta: ApiMeta;
}

export interface NormalizedApiError {
  status: number;
  code: string;
  message: string;
  details?: Record<string, any>;
  raw?: unknown;
}
