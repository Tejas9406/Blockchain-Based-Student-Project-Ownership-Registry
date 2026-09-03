import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';
import { API_BASE_URL, apiClient } from '../services/api';
import { normalizeApiError } from '../utils/error';
import { setAccessToken, clearTokens } from '../utils/token';

describe('Centralized API Client', () => {
  beforeEach(() => {
    clearTokens();
  });

  afterEach(() => {
    clearTokens();
    vi.restoreAllMocks();
  });

  it('configures the expected API base URL', () => {
    expect(API_BASE_URL).toBeDefined();
    expect(apiClient.defaults.baseURL).toBe(API_BASE_URL);
  });

  it('sets default headers and timeout', () => {
    expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
    expect(apiClient.defaults.timeout).toBe(15000);
  });

  it('attaches Bearer token in request headers when access token exists', async () => {
    setAccessToken('test-access-token-123');

    // Simulate interceptor execution
    const requestInterceptor = (apiClient.interceptors.request as any).handlers[0];
    const config = { headers: {} } as any;

    const modifiedConfig = requestInterceptor.fulfilled(config);
    expect(modifiedConfig.headers.Authorization).toBe('Bearer test-access-token-123');
  });

  it('omits Authorization header when no access token exists', async () => {
    clearTokens();

    const requestInterceptor = (apiClient.interceptors.request as any).handlers[0];
    const config = { headers: {} } as any;

    const modifiedConfig = requestInterceptor.fulfilled(config);
    expect(modifiedConfig.headers.Authorization).toBeUndefined();
  });

  describe('Error Normalization Utility', () => {
    it('normalizes structured backend ApiErrorResponse correctly', () => {
      const mockAxiosError = {
        isAxiosError: true,
        response: {
          status: 404,
          data: {
            success: false,
            error: {
              code: 'PROJECT_NOT_FOUND',
              message: 'The requested project identifier does not exist.',
              details: { field: 'project_id', value: 'PRJ-001' },
            },
            meta: { timestamp: '2026-08-31T18:50:00.000Z' },
          },
        },
      };

      vi.spyOn(axios, 'isAxiosError').mockReturnValue(true);

      const normalized = normalizeApiError(mockAxiosError);
      expect(normalized.status).toBe(404);
      expect(normalized.code).toBe('PROJECT_NOT_FOUND');
      expect(normalized.message).toBe('The requested project identifier does not exist.');
      expect(normalized.details).toEqual({ field: 'project_id', value: 'PRJ-001' });
    });

    it('normalizes HTTP 401 Unauthorized errors', () => {
      const mockAxiosError = {
        isAxiosError: true,
        response: {
          status: 401,
          data: {
            success: false,
            error: {
              code: 'UNAUTHORIZED',
              message: 'Invalid or missing authentication credentials.',
            },
          },
        },
      };

      vi.spyOn(axios, 'isAxiosError').mockReturnValue(true);

      const normalized = normalizeApiError(mockAxiosError);
      expect(normalized.status).toBe(401);
      expect(normalized.code).toBe('UNAUTHORIZED');
    });

    it('normalizes network errors without response payload', () => {
      const mockAxiosError = {
        isAxiosError: true,
        message: 'Network Error',
        code: 'ERR_NETWORK',
      };

      vi.spyOn(axios, 'isAxiosError').mockReturnValue(true);

      const normalized = normalizeApiError(mockAxiosError);
      expect(normalized.status).toBe(500);
      expect(normalized.code).toBe('ERR_NETWORK');
      expect(normalized.message).toBe('Network Error');
    });

    it('normalizes timeout errors', () => {
      const mockAxiosError = {
        isAxiosError: true,
        message: 'timeout of 15000ms exceeded',
        code: 'ECONNABORTED',
      };

      vi.spyOn(axios, 'isAxiosError').mockReturnValue(true);

      const normalized = normalizeApiError(mockAxiosError);
      expect(normalized.status).toBe(504);
      expect(normalized.code).toBe('ECONNABORTED');
    });

    it('handles generic non-Axios Error objects', () => {
      vi.spyOn(axios, 'isAxiosError').mockReturnValue(false);

      const genericError = new Error('Custom runtime error');
      const normalized = normalizeApiError(genericError);

      expect(normalized.status).toBe(500);
      expect(normalized.code).toBe('CLIENT_ERROR');
      expect(normalized.message).toBe('Custom runtime error');
    });
  });
});
