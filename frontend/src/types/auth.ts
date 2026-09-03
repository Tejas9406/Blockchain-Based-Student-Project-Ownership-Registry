// Auth domain types matching API_CONTRACT.md Module 1 & FRONTEND_BACKEND_CONTRACT.md

export type UserRole = 'STUDENT' | 'FACULTY' | 'ADMIN' | 'VERIFIER';

export interface UserProfileResponse {
  public_id: string;          // "USR-202608-8F29A"
  email: string;
  full_name: string;
  institution_id: string;
  institution_name?: string | null;
  department: string;
  role: UserRole;
  wallet_address?: string | null;
  is_verified: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface UserSummaryResponse {
  public_id: string;          // "USR-202608-8F29A"
  email: string;
  full_name: string;
  role: UserRole;
  institution_id?: string;
  institution_name?: string | null;
  department?: string | null;
  wallet_address?: string | null;
}

export interface UserRegisterRequest {
  email: string;
  password: string;
  full_name: string;
  institution_id: string;
  institution_name?: string;
  department: string;
  role?: 'STUDENT';
  wallet_address?: string;
}

export interface UserLoginRequest {
  email: string;
  password: string;
}

export interface LoginResponseData {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserSummaryResponse;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponseData {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}
