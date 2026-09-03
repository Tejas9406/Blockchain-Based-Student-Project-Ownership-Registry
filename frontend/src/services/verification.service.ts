import { apiClient } from './api';
import { ApiResponse, VerificationResponseData, VerifyHashRequest } from '../types';

export const verificationService = {
  /**
   * Verifies project version authenticity by registration ID (GET /api/v1/verification/verify-registration/{id}).
   */
  async verifyByRegistrationId(registrationId: string): Promise<VerificationResponseData> {
    const response = await apiClient.get<ApiResponse<VerificationResponseData>>(
      `/verification/verify-registration/${registrationId}`
    );
    return response.data.data;
  },

  /**
   * Verifies project authenticity by raw 64-char SHA-256 hash (POST /api/v1/verification/verify-hash).
   */
  async verifyByHash(payload: VerifyHashRequest): Promise<VerificationResponseData> {
    const response = await apiClient.post<ApiResponse<VerificationResponseData>>(
      '/verification/verify-hash',
      payload
    );
    return response.data.data;
  },

  /**
   * Verifies project authenticity by streaming and hashing uploaded file directly (POST /api/v1/verification/verify-file).
   */
  async verifyByFile(file: File, registrationId?: string): Promise<VerificationResponseData> {
    const formData = new FormData();
    formData.append('file', file);
    if (registrationId) {
      formData.append('registration_id', registrationId);
    }

    const response = await apiClient.post<ApiResponse<VerificationResponseData>>(
      '/verification/verify-file',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data.data;
  },
};
