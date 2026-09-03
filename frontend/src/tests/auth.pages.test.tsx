import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { LoginPage } from '../pages/auth/LoginPage';
import { RegisterPage } from '../pages/auth/RegisterPage';
import { AuthProvider } from '../context/AuthContext';
import { authService } from '../services/auth.service';

describe('Auth Pages — LoginPage & RegisterPage', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('LoginPage', () => {
    it('renders all required form controls and links', () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <LoginPage />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.getByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Create an Account/i })).toBeInTheDocument();
    });

    it('shows client-side validation error when submitting empty email', async () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <LoginPage />
          </AuthProvider>
        </MemoryRouter>
      );

      fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

      expect(await screen.findByText(/Email address is required/i)).toBeInTheDocument();
    });

    it('shows client-side validation error for invalid email format', async () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <LoginPage />
          </AuthProvider>
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/Email Address/i), {
        target: { value: 'invalid-email-format' },
      });
      fireEvent.change(screen.getByLabelText(/Password/i), {
        target: { value: 'password123' },
      });
      fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

      expect(await screen.findByText(/Please enter a valid email address/i)).toBeInTheDocument();
    });

    it('displays API error banner when credentials are invalid', async () => {
      vi.spyOn(authService, 'login').mockRejectedValue({
        status: 401,
        code: 'INVALID_CREDENTIALS',
        message: 'Invalid email or password.',
      });

      render(
        <MemoryRouter>
          <AuthProvider>
            <LoginPage />
          </AuthProvider>
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/Email Address/i), {
        target: { value: 'student@institution.edu' },
      });
      fireEvent.change(screen.getByLabelText(/Password/i), {
        target: { value: 'WrongPass!' },
      });
      fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

      expect(await screen.findByText(/Invalid email or password/i)).toBeInTheDocument();
    });

    it('successfully logs in and navigates to target route', async () => {
      vi.spyOn(authService, 'login').mockResolvedValue({
        access_token: 'valid-access-token',
        refresh_token: 'valid-refresh-token',
        token_type: 'bearer',
        expires_in: 3600,
        user: {
          public_id: 'USR-123',
          email: 'student@institution.edu',
          full_name: 'Tejas Sharma',
          role: 'STUDENT',
          institution_id: 'CS-001',
          department: 'CS',
        },
      });

      render(
        <MemoryRouter initialEntries={['/login']}>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/dashboard" element={<div>Dashboard Destination</div>} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/Email Address/i), {
        target: { value: 'student@institution.edu' },
      });
      fireEvent.change(screen.getByLabelText(/Password/i), {
        target: { value: 'CorrectPassword123!' },
      });
      fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

      await waitFor(() => {
        expect(screen.getByText('Dashboard Destination')).toBeInTheDocument();
      });
    });
  });

  describe('RegisterPage', () => {
    it('renders all required registration fields and labels', () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <RegisterPage />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.getByRole('heading', { name: /Create Account/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/Full Legal Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Student \/ Roll ID/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Department/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Institution Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/EVM Wallet Address/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Register Account/i })).toBeInTheDocument();
    });

    it('validates password length (min 8 characters)', async () => {
      render(
        <MemoryRouter>
          <AuthProvider>
            <RegisterPage />
          </AuthProvider>
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/Full Legal Name/i), {
        target: { value: 'Tejas Sharma' },
      });
      fireEvent.change(screen.getByLabelText(/Email Address/i), {
        target: { value: 'student@institution.edu' },
      });
      fireEvent.change(screen.getByLabelText(/Password/i), {
        target: { value: 'short' },
      });
      fireEvent.change(screen.getByLabelText(/Student \/ Roll ID/i), {
        target: { value: 'CS-001' },
      });
      fireEvent.change(screen.getByLabelText(/Department/i), {
        target: { value: 'CS' },
      });

      fireEvent.click(screen.getByRole('button', { name: /Register Account/i }));

      expect(await screen.findByText(/Password must be at least 8 characters long/i)).toBeInTheDocument();
    });

    it('displays API error banner when registration fails (e.g. duplicate email)', async () => {
      vi.spyOn(authService, 'register').mockRejectedValue({
        status: 409,
        code: 'EMAIL_ALREADY_EXISTS',
        message: 'An account with this email address already exists.',
      });

      render(
        <MemoryRouter>
          <AuthProvider>
            <RegisterPage />
          </AuthProvider>
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/Full Legal Name/i), {
        target: { value: 'Tejas Sharma' },
      });
      fireEvent.change(screen.getByLabelText(/Email Address/i), {
        target: { value: 'duplicate@institution.edu' },
      });
      fireEvent.change(screen.getByLabelText(/Password/i), {
        target: { value: 'ValidPassword123!' },
      });
      fireEvent.change(screen.getByLabelText(/Student \/ Roll ID/i), {
        target: { value: 'CS-001' },
      });
      fireEvent.change(screen.getByLabelText(/Department/i), {
        target: { value: 'Computer Science' },
      });

      fireEvent.click(screen.getByRole('button', { name: /Register Account/i }));

      expect(await screen.findByText(/An account with this email address already exists/i)).toBeInTheDocument();
    });

    it('shows success screen upon successful registration', async () => {
      vi.spyOn(authService, 'register').mockResolvedValue({
        public_id: 'USR-202608-8F29A',
        email: 'student@institution.edu',
        full_name: 'Tejas Sharma',
        institution_id: 'CS-2026-001',
        department: 'Computer Science',
        role: 'STUDENT',
        is_verified: false,
        created_at: '2026-08-31T18:50:00.000Z',
      });

      render(
        <MemoryRouter>
          <AuthProvider>
            <RegisterPage />
          </AuthProvider>
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/Full Legal Name/i), {
        target: { value: 'Tejas Sharma' },
      });
      fireEvent.change(screen.getByLabelText(/Email Address/i), {
        target: { value: 'newstudent@institution.edu' },
      });
      fireEvent.change(screen.getByLabelText(/Password/i), {
        target: { value: 'ValidPassword123!' },
      });
      fireEvent.change(screen.getByLabelText(/Student \/ Roll ID/i), {
        target: { value: 'CS-001' },
      });
      fireEvent.change(screen.getByLabelText(/Department/i), {
        target: { value: 'Computer Science' },
      });

      fireEvent.click(screen.getByRole('button', { name: /Register Account/i }));

      expect(await screen.findByText(/Registration Successful!/i)).toBeInTheDocument();
    });
  });
});
