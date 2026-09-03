import { apiClient } from './api';
import { ApiResponse, ArtifactCategory, ArtifactResponse } from '../types';

export interface UploadArtifactParams {
  file: File;
  artifactCategory?: ArtifactCategory;
  projectId?: string;
  versionId?: string;
}

export const artifactService = {
  /**
   * Uploads an artifact file (POST /api/v1/artifacts/upload) via multipart/form-data.
   */
  async uploadArtifact({
    file,
    artifactCategory = 'OTHER',
    projectId,
    versionId,
  }: UploadArtifactParams): Promise<ArtifactResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('artifact_category', artifactCategory);

    if (projectId) {
      formData.append('project_id', projectId);
    }
    if (versionId) {
      formData.append('version_id', versionId);
    }

    const response = await apiClient.post<ApiResponse<ArtifactResponse>>(
      '/artifacts/upload',
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
