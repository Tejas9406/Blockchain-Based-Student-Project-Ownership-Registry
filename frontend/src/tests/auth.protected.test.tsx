import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from '../app/router';
import { AuthProvider } from '../context/AuthContext';
import { authService } from '../services/auth.service';
import * as tokenUtils from '../utils/token';

describe('Protected Routes & Navigation Flow', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('redirects unauthenticated user from protected route "/dashboard" to "/login"', async () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument();
  });

  it('redirects unauthenticated user from protected route "/projects" to "/login"', async () => {
    render(
      <MemoryRouter initialEntries={['/projects']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument();
  });

  it('allows unauthenticated access to public verification portal "/verify"', async () => {
    render(
      <MemoryRouter initialEntries={['/verify']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(
      screen.getByRole('heading', { name: /Trustless Verification Portal/i })
    ).toBeInTheDocument();
  });

  it('allows unauthenticated access to public verification detail "/verify/:registrationId"', async () => {
    render(
      <MemoryRouter initialEntries={['/verify/REG-2026-TEST']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(
      screen.getByRole('heading', { name: /Ownership Authenticity Dossier/i })
    ).toBeInTheDocument();
  });

  it('allows authenticated user to access protected routes (e.g. "/dashboard", "/projects")', async () => {
    tokenUtils.setAccessToken('valid-jwt-token');
    vi.spyOn(authService, 'getMe').mockResolvedValue({
      public_id: 'USR-202608-8F29A',
      email: 'student@institution.edu',
      full_name: 'Tejas Sharma',
      role: 'STUDENT',
      institution_id: 'CS-001',
      department: 'Computer Science',
    });

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(
      await screen.findByText(/Student Project Registry Dashboard/i)
    ).toBeInTheDocument();
    expect(screen.getByText('Tejas Sharma')).toBeInTheDocument();
    expect(screen.getByText('STUDENT')).toBeInTheDocument();
  });

  it('logs out user via header and redirects to "/login"', async () => {
    tokenUtils.setAccessToken('valid-jwt-token');
    vi.spyOn(authService, 'getMe').mockResolvedValue({
      public_id: 'USR-202608-8F29A',
      email: 'student@institution.edu',
      full_name: 'Tejas Sharma',
      role: 'STUDENT',
      institution_id: 'CS-001',
      department: 'Computer Science',
    });

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(
      await screen.findByText(/Student Project Registry Dashboard/i)
    ).toBeInTheDocument();

    const logoutButton = screen.getByRole('button', { name: /Log Out/i });
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument();
      expect(tokenUtils.getAccessToken()).toBeNull();
    });
  });
});
