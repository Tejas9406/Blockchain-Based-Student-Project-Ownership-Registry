import { apiClient } from './api';
import {
  ApiPaginatedResponse,
  ApiResponse,
  LifecycleStage,
  ProjectCreateRequest,
  ProjectMemberCreateRequest,
  ProjectMemberItem,
  ProjectSummary,
  ProjectVersionCreateRequest,
  ProjectVersionDetail,
} from '../types';

export interface ListProjectsParams {
  page?: number;
  page_size?: number;
  category?: string;
  department?: string;
  lifecycle_stage?: LifecycleStage;
  search?: string;
}

export const projectService = {
  /**
   * Creates a new project (POST /api/v1/projects).
   */
  async createProject(payload: ProjectCreateRequest): Promise<ProjectSummary> {
    const response = await apiClient.post<ApiResponse<ProjectSummary>>(
      '/projects',
      payload
    );
    return response.data.data;
  },

  /**
   * Lists projects with pagination and filters (GET /api/v1/projects).
   */
  async listProjects(params?: ListProjectsParams): Promise<ApiPaginatedResponse<ProjectSummary>> {
    const response = await apiClient.get<ApiPaginatedResponse<ProjectSummary>>(
      '/projects',
      { params }
    );
    return response.data;
  },

  /**
   * Retrieves project details by public ID or slug (GET /api/v1/projects/{id}).
   */
  async getProject(projectIdOrSlug: string): Promise<ProjectSummary> {
    const response = await apiClient.get<ApiResponse<ProjectSummary>>(
      `/projects/${projectIdOrSlug}`
    );
    return response.data.data;
  },

  /**
   * Lists members of a project (GET /api/v1/projects/{id}/members).
   */
  async listMembers(projectId: string): Promise<ProjectMemberItem[]> {
    const response = await apiClient.get<ApiResponse<ProjectMemberItem[]>>(
      `/projects/${projectId}/members`
    );
    return response.data.data;
  },

  /**
   * Adds/invites a member to a project (POST /api/v1/projects/{id}/members).
   */
  async addMember(
    projectId: string,
    payload: ProjectMemberCreateRequest
  ): Promise<ProjectMemberItem> {
    const response = await apiClient.post<ApiResponse<ProjectMemberItem>>(
      `/projects/${projectId}/members`,
      payload
    );
    return response.data.data;
  },

  /**
   * Creates and anchors a project version milestone (POST /api/v1/projects/{id}/versions).
   */
  async createVersion(
    projectId: string,
    payload: ProjectVersionCreateRequest,
    idempotencyKey?: string
  ): Promise<ProjectVersionDetail> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }

    const response = await apiClient.post<ApiResponse<ProjectVersionDetail>>(
      `/projects/${projectId}/versions`,
      payload,
      { headers }
    );
    return response.data.data;
  },

  /**
   * Lists all version milestones for a project (GET /api/v1/projects/{id}/versions).
   */
  async listVersions(projectId: string): Promise<ProjectVersionDetail[]> {
    const response = await apiClient.get<ApiResponse<ProjectVersionDetail[]>>(
      `/projects/${projectId}/versions`
    );
    return response.data.data;
  },
};
