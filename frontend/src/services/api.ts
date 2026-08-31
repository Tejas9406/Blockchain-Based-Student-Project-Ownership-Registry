import axios from 'axios';

// Ensure API base URL comes from environment variables, fallback to local default
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export interface HealthCheckResponse {
  status: string;
  service: string;
  environment?: string;
  database?: string;
}

export const checkBackendHealth = async (): Promise<HealthCheckResponse> => {
  const response = await apiClient.get<HealthCheckResponse>('/health');
  return response.data;
};
