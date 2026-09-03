import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import React from 'react';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { authService } from '../services/auth.service';
import * as tokenUtils from '../utils/token';
import { UserSummaryResponse, LoginResponseData, UserProfileResponse } from '../types';

describe('AuthContext & useAuth', () => {
  const mockUser: UserSummaryResponse = {
    public_id: 'USR-202608-8F29A',
    email: 'student@institution.edu',
    full_name: 'Tejas Sharma',
    role: 'STUDENT',
    institution_id: 'CS-2026-001',
    department: 'Computer Science',
  };

  const mockLoginData: LoginResponseData = {
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    token_type: 'bearer',
    expires_in: 3600,
    user: mockUser,
  };

  const mockProfile: UserProfileResponse = {
    public_id: 'USR-202608-8F29A',
    email: 'student@institution.edu',
    full_name: 'Tejas Sharma',
    institution_id: 'CS-2026-001',
    institution_name: 'National Institute of Technology',
    department: 'Computer Science',
    role: 'STUDENT',
    wallet_address: null,
    is_verified: true,
    created_at: '2026-08-31T18:50:00.000Z',
  };

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('initializes in unauthenticated state when no token is present', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('restores session when access token exists and /auth/me succeeds', async () => {
    tokenUtils.setAccessToken('valid-jwt-token');
    vi.spyOn(authService, 'getMe').mockResolvedValue(mockUser);

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    // Wait for effect to finish loading
    await act(async () => {
      await result.current.refreshUser();
    });

    expect(authService.getMe).toHaveBeenCalled();
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isLoading).toBe(false);
  });

  it('clears token and marks unauthenticated when /auth/me fails (e.g. 401)', async () => {
    tokenUtils.setAccessToken('expired-jwt-token');
    vi.spyOn(authService, 'getMe').mockRejectedValue({
      status: 401,
      code: 'UNAUTHORIZED',
      message: 'Token expired',
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.refreshUser();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(tokenUtils.getAccessToken()).toBeNull();
  });

  it('logs in successfully and sets authentication state and tokens', async () => {
    vi.spyOn(authService, 'login').mockResolvedValue(mockLoginData);

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      const response = await result.current.login({
        email: 'student@institution.edu',
        password: 'Password123!',
      });
      expect(response).toEqual(mockLoginData);
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(mockUser);
    expect(tokenUtils.getAccessToken()).toBe('mock-access-token');
    expect(tokenUtils.getRefreshToken()).toBe('mock-refresh-token');
  });

  it('handles login failure gracefully without setting auth state', async () => {
    vi.spyOn(authService, 'login').mockRejectedValue({
      status: 401,
      code: 'INVALID_CREDENTIALS',
      message: 'Invalid email or password',
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await expect(
      act(async () => {
        await result.current.login({
          email: 'wrong@institution.edu',
          password: 'WrongPassword!',
        });
      })
    ).rejects.toBeDefined();

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(tokenUtils.getAccessToken()).toBeNull();
  });

  it('registers successfully and returns public profile', async () => {
    vi.spyOn(authService, 'register').mockResolvedValue(mockProfile);

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      const profile = await result.current.register({
        full_name: 'Tejas Sharma',
        email: 'student@institution.edu',
        password: 'Password123!',
        institution_id: 'CS-2026-001',
        department: 'Computer Science',
      });
      expect(profile).toEqual(mockProfile);
    });

    expect(authService.register).toHaveBeenCalled();
  });

  it('logs out and removes tokens and current user state', async () => {
    tokenUtils.setAccessToken('mock-access-token');
    tokenUtils.setRefreshToken('mock-refresh-token');
    vi.spyOn(authService, 'getMe').mockResolvedValue(mockUser);

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.refreshUser();
    });

    expect(result.current.isAuthenticated).toBe(true);

    act(() => {
      result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(tokenUtils.getAccessToken()).toBeNull();
    expect(tokenUtils.getRefreshToken()).toBeNull();
  });
});
