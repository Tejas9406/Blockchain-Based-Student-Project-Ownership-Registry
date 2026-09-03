import { apiClient } from './api';
import {
  ApiResponse,
  LoginResponseData,
  RefreshTokenRequest,
  RefreshTokenResponseData,
  UserProfileResponse,
  UserRegisterRequest,
  UserLoginRequest,
  UserSummaryResponse,
} from '../types';

export const authService = {
  /**
   * Registers a new user account (POST /api/v1/auth/register).
   */
  async register(payload: UserRegisterRequest): Promise<UserProfileResponse> {
    const response = await apiClient.post<ApiResponse<UserProfileResponse>>(
      '/auth/register',
      payload
    );
    return response.data.data;
  },

  /**
   * Logs in a user and returns tokens (POST /api/v1/auth/login).
   */
  async login(payload: UserLoginRequest): Promise<LoginResponseData> {
    const response = await apiClient.post<ApiResponse<LoginResponseData>>(
      '/auth/login',
      payload
    );
    return response.data.data;
  },

  /**
   * Refreshes the access token (POST /api/v1/auth/refresh).
   */
  async refreshToken(payload: RefreshTokenRequest): Promise<RefreshTokenResponseData> {
    const response = await apiClient.post<ApiResponse<RefreshTokenResponseData>>(
      '/auth/refresh',
      payload
    );
    return response.data.data;
  },

  /**
   * Retrieves the current user's profile summary (GET /api/v1/auth/me).
   */
  async getMe(): Promise<UserSummaryResponse> {
    const response = await apiClient.get<ApiResponse<UserSummaryResponse>>(
      '/auth/me'
    );
    return response.data.data;
  },
};
