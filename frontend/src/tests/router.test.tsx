import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from '../app/router';
import { AuthProvider } from '../context/AuthContext';
import { authService } from '../services/auth.service';
import * as tokenUtils from '../utils/token';

import { projectService } from '../services/project.service';

describe('React Router & Auth Route Guards', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('Public Routes', () => {
    it('renders LoginPage on "/login"', () => {
      render(
        <MemoryRouter initialEntries={['/login']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.getByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument();
    });

    it('renders RegisterPage on "/register"', () => {
      render(
        <MemoryRouter initialEntries={['/register']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.getByRole('heading', { name: /Create Account/i })).toBeInTheDocument();
    });

    it('renders VerificationPortalPage on "/verify"', () => {
      render(
        <MemoryRouter initialEntries={['/verify']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.getByRole('heading', { name: /Trustless Verification Portal/i })).toBeInTheDocument();
    });

    it('renders VerificationDetailPage on "/verify/:registrationId"', () => {
      render(
        <MemoryRouter initialEntries={['/verify/REG-2026-A8F92D']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.getByRole('heading', { name: /Ownership Authenticity Dossier/i })).toBeInTheDocument();
    });

    it('renders NotFoundPage on unknown routes', () => {
      render(
        <MemoryRouter initialEntries={['/some/unknown/route']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.getByRole('heading', { name: /Page Not Found/i })).toBeInTheDocument();
    });
  });

  describe('Protected Routes (Authenticated)', () => {
    const setupAuthenticatedUser = () => {
      tokenUtils.setAccessToken('valid-jwt-token');
      vi.spyOn(authService, 'getMe').mockResolvedValue({
        public_id: 'USR-202608-8F29A',
        email: 'student@institution.edu',
        full_name: 'Tejas Sharma',
        role: 'STUDENT',
        institution_id: 'CS-2026-001',
        department: 'Computer Science',
      });
      vi.spyOn(projectService, 'getProject').mockResolvedValue({
        public_id: 'PRJ-123',
        slug: 'prj-123-slug',
        title: 'Project 123 Workspace',
        abstract: 'Test project workspace',
        category: 'Blockchain',
        department: 'Computer Science',
        academic_year: '2025-2026',
        current_lifecycle_stage: 'DESIGN',
        visibility: 'PUBLIC',
        status: 'ACTIVE',
        created_at: '2026-08-31T18:50:00.000Z',
      });
      vi.spyOn(projectService, 'listProjects').mockResolvedValue({
        success: true,
        data: [],
        meta: {
          page: 1,
          page_size: 12,
          total_items: 0,
          total_pages: 0,
          has_next: false,
          has_prev: false,
          timestamp: '2026-08-31T18:50:00.000Z',
        },
      });
      vi.spyOn(projectService, 'listMembers').mockResolvedValue([]);
      vi.spyOn(projectService, 'listVersions').mockResolvedValue([]);
    };

    it('redirects root "/" to DashboardPage when authenticated', async () => {
      setupAuthenticatedUser();

      render(
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(await screen.findByText(/Welcome back,/i)).toBeInTheDocument();
    });

    it('renders ProjectsListPage on "/projects" when authenticated', async () => {
      setupAuthenticatedUser();

      render(
        <MemoryRouter initialEntries={['/projects']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(await screen.findByRole('heading', { name: /Academic Project Catalog/i })).toBeInTheDocument();
    });

    it('renders NewProjectPage on "/projects/new" when authenticated', async () => {
      setupAuthenticatedUser();

      render(
        <MemoryRouter initialEntries={['/projects/new']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(await screen.findByRole('heading', { name: /Register New Project/i })).toBeInTheDocument();
    });

    it('renders ProjectDetailPage on "/projects/:projectId" when authenticated', async () => {
      setupAuthenticatedUser();

      render(
        <MemoryRouter initialEntries={['/projects/PRJ-123']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(await screen.findByText(/PROJECT ID: PRJ-123/i)).toBeInTheDocument();
    });

    it('renders ProjectArtifactsPage on "/projects/:projectId/artifacts" when authenticated', async () => {
      setupAuthenticatedUser();

      render(
        <MemoryRouter initialEntries={['/projects/PRJ-123/artifacts']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(await screen.findByRole('heading', { name: /Project 123 Workspace/i })).toBeInTheDocument();
      expect(await screen.findByRole('heading', { name: /Ingested Artifacts/i })).toBeInTheDocument();
    });

    it('renders ProjectVersionsPage on "/projects/:projectId/versions" when authenticated', async () => {
      setupAuthenticatedUser();

      render(
        <MemoryRouter initialEntries={['/projects/PRJ-123/versions']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(await screen.findByRole('heading', { name: /Project Milestones & Version Snapshots/i })).toBeInTheDocument();
    });

    it('renders DisputesPage on "/disputes" when authenticated', async () => {
      setupAuthenticatedUser();

      render(
        <MemoryRouter initialEntries={['/disputes']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(await screen.findByRole('heading', { name: /Ownership Claims & Dispute Registry/i })).toBeInTheDocument();
    });

    it('renders CertificateDetailPage on "/certificates/:registrationId" when authenticated', async () => {
      setupAuthenticatedUser();

      render(
        <MemoryRouter initialEntries={['/certificates/REG-2026-A8F92D']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(await screen.findByRole('heading', { name: /Ownership Certificate Preview/i })).toBeInTheDocument();
    });
  });
});
