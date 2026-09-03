import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as tokenUtils from '../utils/token';
import { apiClient } from '../services/api';

describe('Authentication Security Specifications', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('stores and retrieves access and refresh tokens safely in localStorage', () => {
    tokenUtils.setAccessToken('secret-access-token-123');
    tokenUtils.setRefreshToken('secret-refresh-token-456');

    expect(tokenUtils.getAccessToken()).toBe('secret-access-token-123');
    expect(tokenUtils.getRefreshToken()).toBe('secret-refresh-token-456');

    tokenUtils.clearTokens();

    expect(tokenUtils.getAccessToken()).toBeNull();
    expect(tokenUtils.getRefreshToken()).toBeNull();
  });

  it('attaches Authorization header only when token exists', async () => {
    tokenUtils.setAccessToken('my-secure-token');

    // Test axios interceptor on apiClient
    const config = await (apiClient.interceptors.request as any).handlers[0].fulfilled({
      headers: {},
    });

    expect(config.headers.Authorization).toBe('Bearer my-secure-token');
  });

  it('omits Authorization header when token is empty or removed', async () => {
    tokenUtils.clearTokens();

    const config = await (apiClient.interceptors.request as any).handlers[0].fulfilled({
      headers: {},
    });

    expect(config.headers.Authorization).toBeUndefined();
  });

  it('handles corrupted or restricted localStorage without unhandled exceptions', () => {
    const originalGetItem = localStorage.getItem;
    localStorage.getItem = () => {
      throw new Error('SecurityError: Access is denied');
    };

    expect(() => tokenUtils.getAccessToken()).not.toThrow();
    expect(tokenUtils.getAccessToken()).toBeNull();

    localStorage.getItem = originalGetItem;
  });
});
