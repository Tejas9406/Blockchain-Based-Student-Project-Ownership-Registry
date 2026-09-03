import axios from 'axios';
import { ApiErrorResponse, NormalizedApiError } from '../types/api';

/**
 * Normalizes any error (AxiosError, ApiErrorResponse, Error, or unknown)
 * into a standard NormalizedApiError object.
 */
export function normalizeApiError(error: unknown): NormalizedApiError {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status || (error.code === 'ECONNABORTED' ? 504 : 500);
    const data = error.response?.data as ApiErrorResponse | undefined;

    if (data && typeof data === 'object' && 'error' in data && data.error) {
      return {
        status,
        code: data.error.code || `HTTP_${status}`,
        message: data.error.message || error.message || 'An error occurred.',
        details: data.error.details,
        raw: error,
      };
    }

    return {
      status,
      code: error.code || `HTTP_${status}`,
      message: error.message || 'Network request failed.',
      raw: error,
    };
  }

  if (error instanceof Error) {
    return {
      status: 500,
      code: 'CLIENT_ERROR',
      message: error.message,
      raw: error,
    };
  }

  return {
    status: 500,
    code: 'UNKNOWN_ERROR',
    message: 'An unexpected error occurred.',
    raw: error,
  };
}
