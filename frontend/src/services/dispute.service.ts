import { apiClient } from './api';
import {
  ApiResponse,
  DisputeAdjudicateRequest,
  DisputeCreateRequest,
  DisputeDetailResponse,
} from '../types';

export const disputeService = {
  /**
   * Raises a new ownership dispute (POST /api/v1/disputes).
   */
  async raiseDispute(payload: DisputeCreateRequest): Promise<DisputeDetailResponse> {
    const response = await apiClient.post<ApiResponse<DisputeDetailResponse>>(
      '/disputes',
      payload
    );
    return response.data.data;
  },

  /**
   * Retrieves details of a specific dispute by ID (GET /api/v1/disputes/{id}).
   */
  async getDispute(disputeId: string): Promise<DisputeDetailResponse> {
    const response = await apiClient.get<ApiResponse<DisputeDetailResponse>>(
      `/disputes/${disputeId}`
    );
    return response.data.data;
  },

  /**
   * Lists all disputes associated with a project (GET /api/v1/disputes/project/{projectId}).
   */
  async listProjectDisputes(projectId: string): Promise<DisputeDetailResponse[]> {
    const response = await apiClient.get<ApiResponse<DisputeDetailResponse[]>>(
      `/disputes/project/${projectId}`
    );
    return response.data.data;
  },

  /**
   * Adjudicates an active dispute (Admin only) (PATCH /api/v1/admin/disputes/{disputeId}/adjudicate).
   */
  async adjudicateDispute(
    disputeId: string,
    payload: DisputeAdjudicateRequest
  ): Promise<DisputeDetailResponse> {
    const response = await apiClient.patch<ApiResponse<DisputeDetailResponse>>(
      `/admin/disputes/${disputeId}/adjudicate`,
      payload
    );
    return response.data.data;
  },
};
