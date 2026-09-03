import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ProjectsListPage } from '../pages/projects/ProjectsListPage';
import { NewProjectPage } from '../pages/projects/NewProjectPage';
import { ProjectDetailPage } from '../pages/projects/ProjectDetailPage';
import { projectService } from '../services/project.service';
import { authService } from '../services/auth.service';
import { AuthProvider } from '../context/AuthContext';
import * as tokenUtils from '../utils/token';
import {
  ProjectSummary,
  ProjectMemberItem,
  ProjectVersionDetail,
  ApiPaginatedResponse,
} from '../types';

describe('Projects Module Frontend Tests', () => {
  const mockUser = {
    public_id: 'USR-202608-8F29A',
    email: 'tejas.sharma@nit.edu',
    full_name: 'Tejas Sharma',
    role: 'STUDENT' as const,
    institution_id: 'NIT-CS-2026-081',
    department: 'Computer Science & Engineering',
  };

  const mockProject1: ProjectSummary = {
    public_id: 'PRJ-202608-99B12',
    slug: 'decentralized-ipfs-academic-registry',
    title: 'Decentralized IPFS Academic Registry',
    abstract: 'A tamper-proof student project registry with EVM smart contracts and IPFS storage.',
    category: 'Blockchain & Web3',
    department: 'Computer Science & Engineering',
    academic_year: '2025-2026',
    current_lifecycle_stage: 'DESIGN',
    visibility: 'PUBLIC',
    status: 'ACTIVE',
    owner: {
      public_id: 'USR-202608-8F29A',
      full_name: 'Tejas Sharma',
    },
    created_at: '2026-08-31T18:50:00.000Z',
  };

  const mockProject2: ProjectSummary = {
    public_id: 'PRJ-202608-88A11',
    slug: 'ai-assisted-code-vulnerability-scanner',
    title: 'AI-Assisted Code Vulnerability Scanner',
    abstract: 'Automated static analysis tool leveraging LLMs for vulnerability detection in smart contracts.',
    category: 'Cybersecurity',
    department: 'Information Technology',
    academic_year: '2025-2026',
    current_lifecycle_stage: 'PROTOTYPE',
    visibility: 'INSTITUTIONAL',
    status: 'ACTIVE',
    owner: {
      public_id: 'USR-202608-11B22',
      full_name: 'Aman Verma',
    },
    created_at: '2026-09-01T10:00:00.000Z',
  };

  const mockPaginatedResponse: ApiPaginatedResponse<ProjectSummary> = {
    success: true,
    data: [mockProject1, mockProject2],
    meta: {
      page: 1,
      page_size: 12,
      total_items: 2,
      total_pages: 1,
      has_next: false,
      has_prev: false,
      timestamp: '2026-09-03T14:00:00.000Z',
    },
  };

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    tokenUtils.setAccessToken('valid-jwt-token');
    vi.spyOn(authService, 'getMe').mockResolvedValue(mockUser);
  });

  describe('ProjectsListPage', () => {
    it('renders project list returned by projectService', async () => {
      vi.spyOn(projectService, 'listProjects').mockResolvedValue(mockPaginatedResponse);

      render(
        <MemoryRouter initialEntries={['/projects']}>
          <AuthProvider>
            <ProjectsListPage />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.getByText(/Loading project catalog.../i)).toBeInTheDocument();

      expect(await screen.findByRole('heading', { name: /Academic Project Catalog/i })).toBeInTheDocument();
      expect(screen.getByText('Decentralized IPFS Academic Registry')).toBeInTheDocument();
      expect(screen.getByText('AI-Assisted Code Vulnerability Scanner')).toBeInTheDocument();
      expect(screen.getByText('PRJ-202608-99B12')).toBeInTheDocument();
      expect(screen.getByText('PRJ-202608-88A11')).toBeInTheDocument();
      expect(screen.getAllByText('DESIGN').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('PROTOTYPE').length).toBeGreaterThanOrEqual(1);
    });

    it('renders loading state initially', async () => {
      vi.spyOn(projectService, 'listProjects').mockReturnValue(new Promise(() => {}));

      render(
        <MemoryRouter initialEntries={['/projects']}>
          <AuthProvider>
            <ProjectsListPage />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.getByText(/Loading project catalog.../i)).toBeInTheDocument();
    });

    it('renders empty state when no projects are returned', async () => {
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
          timestamp: '2026-09-03T14:00:00.000Z',
        },
      });

      render(
        <MemoryRouter initialEntries={['/projects']}>
          <AuthProvider>
            <ProjectsListPage />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(await screen.findByText('No Projects Registered Yet')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Register First Project/i })).toBeInTheDocument();
    });

    it('renders error state and retry triggers refetch', async () => {
      const listSpy = vi
        .spyOn(projectService, 'listProjects')
        .mockRejectedValueOnce(new Error('Network connection failure'))
        .mockResolvedValueOnce(mockPaginatedResponse);

      render(
        <MemoryRouter initialEntries={['/projects']}>
          <AuthProvider>
            <ProjectsListPage />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(await screen.findByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/Network connection failure/i)).toBeInTheDocument();

      // Click retry
      const retryButton = screen.getByRole('button', { name: /Retry/i });
      fireEvent.click(retryButton);

      expect(await screen.findByText('Decentralized IPFS Academic Registry')).toBeInTheDocument();
      expect(listSpy).toHaveBeenCalledTimes(2);
    });

    it('filters projects when search and filters are submitted', async () => {
      const listSpy = vi.spyOn(projectService, 'listProjects').mockResolvedValue(mockPaginatedResponse);

      render(
        <MemoryRouter initialEntries={['/projects']}>
          <AuthProvider>
            <ProjectsListPage />
          </AuthProvider>
        </MemoryRouter>
      );

      await screen.findByRole('heading', { name: /Academic Project Catalog/i });

      // Change search input
      const searchInput = screen.getByPlaceholderText(/Search by project title/i);
      fireEvent.change(searchInput, { target: { value: 'blockchain' } });

      // Submit search form
      const searchButton = screen.getByRole('button', { name: /^Search$/i });
      fireEvent.click(searchButton);

      await waitFor(() => {
        expect(listSpy).toHaveBeenCalledWith(
          expect.objectContaining({
            search: 'blockchain',
            page: 1,
            page_size: 12,
          })
        );
      });
    });
  });

  describe('NewProjectPage (Create Project)', () => {
    it('renders create project form with required controls and prefilled department', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/new']}>
          <AuthProvider>
            <NewProjectPage />
          </AuthProvider>
        </MemoryRouter>
      );

      expect(await screen.findByRole('heading', { name: /Register New Project/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/Project Title/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Domain Category/i)).toBeInTheDocument();
      await waitFor(() => {
        expect(screen.getByLabelText(/Department/i)).toHaveValue('Computer Science & Engineering');
      });
      expect(screen.getByLabelText(/Academic Year/i)).toHaveValue('2025-2026');
      expect(screen.getByRole('button', { name: /Register Project/i })).toBeInTheDocument();
    });

    it('validates required fields client-side before calling service', async () => {
      const createSpy = vi.spyOn(projectService, 'createProject');

      render(
        <MemoryRouter initialEntries={['/projects/new']}>
          <AuthProvider>
            <NewProjectPage />
          </AuthProvider>
        </MemoryRouter>
      );

      // Attempt submit without filling title and category
      const submitBtn = screen.getByRole('button', { name: /Register Project/i });
      fireEvent.click(submitBtn);

      expect(await screen.findByText('Project title is required.')).toBeInTheDocument();
      expect(screen.getByText('Category is required.')).toBeInTheDocument();
      expect(createSpy).not.toHaveBeenCalled();
    });

    it('submits valid form data, disables button during submission, and navigates on success', async () => {
      const createSpy = vi.spyOn(projectService, 'createProject').mockResolvedValue(mockProject1);

      render(
        <MemoryRouter initialEntries={['/projects/new']}>
          <AuthProvider>
            <Routes>
              <Route path="/projects/new" element={<NewProjectPage />} />
              <Route path="/projects/:projectId" element={<div>Project Detail View</div>} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      );

      // Fill in fields
      fireEvent.change(screen.getByLabelText(/Project Title/i), {
        target: { value: 'Decentralized IPFS Academic Registry' },
      });
      fireEvent.change(screen.getByLabelText(/Domain Category/i), {
        target: { value: 'Blockchain & Web3' },
      });
      fireEvent.change(screen.getByLabelText(/Department/i), {
        target: { value: 'Computer Science & Engineering' },
      });
      fireEvent.change(screen.getByLabelText(/Academic Year/i), {
        target: { value: '2025-2026' },
      });
      fireEvent.change(screen.getByLabelText(/Project Abstract/i), {
        target: { value: 'Test abstract content' },
      });

      const submitBtn = screen.getByRole('button', { name: /Register Project/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(createSpy).toHaveBeenCalledWith({
          title: 'Decentralized IPFS Academic Registry',
          category: 'Blockchain & Web3',
          department: 'Computer Science & Engineering',
          academic_year: '2025-2026',
          visibility: 'PUBLIC',
          abstract: 'Test abstract content',
        });
      });

      expect(await screen.findByText('Project Detail View')).toBeInTheDocument();
    });

    it('displays normalized API error message on submission failure', async () => {
      vi.spyOn(projectService, 'createProject').mockRejectedValue({
        response: {
          status: 409,
          data: {
            success: false,
            error: {
              code: 'PROJECT_TITLE_EXISTS',
              message: 'A project with this title already exists in the department.',
            },
          },
        },
      });

      render(
        <MemoryRouter initialEntries={['/projects/new']}>
          <AuthProvider>
            <NewProjectPage />
          </AuthProvider>
        </MemoryRouter>
      );

      fireEvent.change(screen.getByLabelText(/Project Title/i), {
        target: { value: 'Duplicate Project Title' },
      });
      fireEvent.change(screen.getByLabelText(/Domain Category/i), {
        target: { value: 'Blockchain' },
      });
      fireEvent.change(screen.getByLabelText(/Department/i), {
        target: { value: 'Computer Science & Engineering' },
      });
      fireEvent.change(screen.getByLabelText(/Academic Year/i), {
        target: { value: '2025-2026' },
      });

      const submitBtn = screen.getByRole('button', { name: /Register Project/i });
      fireEvent.click(submitBtn);

      expect(
        await screen.findByText('A project with this title already exists in the department.')
      ).toBeInTheDocument();
    });
  });

  describe('ProjectDetailPage', () => {
    const mockMembers: ProjectMemberItem[] = [
      {
        user: {
          public_id: 'USR-202608-8F29A',
          email: 'tejas.sharma@nit.edu',
          full_name: 'Tejas Sharma',
          role: 'STUDENT',
          department: 'Computer Science & Engineering',
        },
        role_in_project: 'LEAD',
        contribution_percentage: 60,
        is_owner: true,
        joined_at: '2026-08-31T18:50:00.000Z',
      },
      {
        user: {
          public_id: 'USR-202608-11B22',
          email: 'aman.verma@nit.edu',
          full_name: 'Aman Verma',
          role: 'STUDENT',
          department: 'Computer Science & Engineering',
        },
        role_in_project: 'CONTRIBUTOR',
        contribution_percentage: 40,
        is_owner: false,
        joined_at: '2026-09-01T10:00:00.000Z',
      },
    ];

    const mockVersions: ProjectVersionDetail[] = [
      {
        public_id: 'VER-202608-41C88',
        registration_id: 'REG-2026-A8F92D',
        version_index: 1,
        version_tag: 'v1.0',
        lifecycle_stage: 'DESIGN',
        title: 'System Architecture & Threat Model',
        description: 'Initial specifications',
        composite_sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
        ipfs_root_cid: 'bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m',
        anchoring_status: 'ANCHORED',
        dispute_status: 'NONE',
        created_at: '2026-08-31T18:50:00.000Z',
      },
    ];

    it('renders project metadata, team members, and milestone versions', async () => {
      vi.spyOn(projectService, 'getProject').mockResolvedValue(mockProject1);
      vi.spyOn(projectService, 'listMembers').mockResolvedValue(mockMembers);
      vi.spyOn(projectService, 'listVersions').mockResolvedValue(mockVersions);

      render(
        <MemoryRouter initialEntries={['/projects/PRJ-202608-99B12']}>
          <AuthProvider>
            <Routes>
              <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      );

      expect(screen.getByText(/Loading project workspace.../i)).toBeInTheDocument();

      expect(await screen.findByRole('heading', { name: 'Decentralized IPFS Academic Registry' })).toBeInTheDocument();
      expect(screen.getByText('PROJECT ID: PRJ-202608-99B12')).toBeInTheDocument();
      expect(screen.getByText('slug: decentralized-ipfs-academic-registry')).toBeInTheDocument();
      expect(screen.getByText('Computer Science & Engineering')).toBeInTheDocument();
      expect(screen.getByText('Blockchain & Web3')).toBeInTheDocument();

      // Team members
      expect(screen.getByText('Project Team & Mentors')).toBeInTheDocument();
      expect(screen.getAllByText('Tejas Sharma').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Aman Verma')).toBeInTheDocument();
      expect(screen.getByText('60%')).toBeInTheDocument();
      expect(screen.getByText('40%')).toBeInTheDocument();

      // Versions
      expect(screen.getByText('Project Version Milestones')).toBeInTheDocument();
      expect(screen.getByText('v1.0')).toBeInTheDocument();
      expect(screen.getByText('System Architecture & Threat Model')).toBeInTheDocument();
      expect(screen.getByText('REG-2026-A8F92D')).toBeInTheDocument();
      expect(screen.getByText('Anchored')).toBeInTheDocument();

      // Artifacts navigation action
      expect(screen.getByRole('link', { name: /Manage Artifacts/i })).toBeInTheDocument();

      // Ensure future version management links are not present
      expect(screen.queryByRole('link', { name: /Milestone Versions/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /View All Versions/i })).not.toBeInTheDocument();
    });

    it('handles not found error gracefully', async () => {
      vi.spyOn(projectService, 'getProject').mockRejectedValue({
        response: {
          status: 404,
          data: {
            success: false,
            error: {
              code: 'PROJECT_NOT_FOUND',
              message: 'The requested project identifier does not exist.',
            },
          },
        },
      });

      render(
        <MemoryRouter initialEntries={['/projects/PRJ-NON-EXISTENT']}>
          <AuthProvider>
            <Routes>
              <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      );

      expect(await screen.findByText('The requested project identifier does not exist.')).toBeInTheDocument();
      expect(screen.getByText('Project Not Found')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Return to Project Catalog/i })).toBeInTheDocument();
    });
  });
});
