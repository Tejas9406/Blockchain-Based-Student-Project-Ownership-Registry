import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ProjectDetailPage } from '../pages/projects/ProjectDetailPage';
import { ProjectMemberCard } from '../components/projects/ProjectMemberCard';
import { AddMemberModal } from '../components/projects/AddMemberModal';
import { ProjectTeamSection } from '../components/projects/ProjectTeamSection';
import { projectService } from '../services/project.service';
import { AuthContext, AuthContextType } from '../context/AuthContext';
import { ProjectMemberItem, ProjectSummary } from '../types';

// Mock clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockImplementation(() => Promise.resolve()),
  },
});

// Mock project service
vi.mock('../services/project.service', () => ({
  projectService: {
    getProject: vi.fn(),
    listMembers: vi.fn(),
    addMember: vi.fn(),
    listVersions: vi.fn(),
  },
}));

const mockOwnerMember: ProjectMemberItem = {
  user: {
    public_id: 'USR-202609-OWNER1',
    email: 'creator@sih2026.edu',
    full_name: 'Aarav Sharma',
    institution_id: 'INST-IITB-101',
    institution_name: 'IIT Bombay',
    department: 'Computer Science',
    role: 'STUDENT',
    wallet_address: '0x1234567890abcdef1234567890abcdef12345678',
    is_verified: true,
    created_at: '2026-08-01T10:00:00Z',
  },
  role_in_project: 'LEAD',
  contribution_percentage: 50.0,
  is_owner: true,
  joined_at: '2026-08-01T10:00:00Z',
};

const mockContributorMember: ProjectMemberItem = {
  user: {
    public_id: 'USR-202609-CONTRIB',
    email: 'contributor@sih2026.edu',
    full_name: 'Diya Patel',
    institution_id: 'INST-IITB-102',
    institution_name: 'IIT Bombay',
    department: 'Computer Science',
    role: 'STUDENT',
    is_verified: true,
    created_at: '2026-08-05T12:00:00Z',
  },
  role_in_project: 'CONTRIBUTOR',
  contribution_percentage: 25.5,
  is_owner: false,
  joined_at: '2026-08-05T12:00:00Z',
};

const mockMentorMember: ProjectMemberItem = {
  user: {
    public_id: 'USR-202609-MENTOR1',
    email: 'mentor.prof@sih2026.edu',
    full_name: 'Dr. Rajesh Verma',
    institution_id: 'INST-IITB-900',
    institution_name: 'IIT Bombay',
    department: 'Electrical Engineering',
    role: 'FACULTY',
    is_verified: true,
    created_at: '2026-07-01T08:00:00Z',
  },
  role_in_project: 'FACULTY_MENTOR',
  contribution_percentage: 10.0,
  is_owner: false,
  joined_at: '2026-08-10T14:30:00Z',
};

const mockProject: ProjectSummary = {
  public_id: 'PRJ-202609-A8F92',
  slug: 'decentralized-academic-provenance',
  title: 'Decentralized Academic Provenance Protocol',
  abstract: 'A tamper-proof system for registering student research and software artifacts on-chain.',
  category: 'BLOCKCHAIN_SECURITY',
  department: 'Computer Science',
  academic_year: '2025-2026',
  current_lifecycle_stage: 'PROTOTYPE',
  visibility: 'PUBLIC',
  status: 'ACTIVE',
  owner: {
    public_id: 'USR-202609-OWNER1',
    full_name: 'Aarav Sharma',
  },
  created_at: '2026-08-01T10:00:00Z',
};

const createMockAuthContext = (overrides?: Partial<AuthContextType>): AuthContextType => ({
  user: {
    public_id: 'USR-202609-OWNER1',
    email: 'creator@sih2026.edu',
    full_name: 'Aarav Sharma',
    role: 'STUDENT',
    institution_id: 'INST-IITB-101',
    department: 'Computer Science',
  },
  isAuthenticated: true,
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  refreshUser: vi.fn(),
  ...overrides,
});

describe('Frontend Project Team / Member Management Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1. Member list renders and details render correctly
  it('renders member cards with full name, email, department, institution, and avatar', () => {
    render(<ProjectMemberCard member={mockContributorMember} />);

    expect(screen.getByText('Diya Patel')).toBeInTheDocument();
    expect(screen.getByText('contributor@sih2026.edu')).toBeInTheDocument();
    expect(screen.getByText(/Computer Science • IIT Bombay/i)).toBeInTheDocument();
    expect(screen.getByText('25.5%')).toBeInTheDocument();
    expect(screen.getByText('Contributor')).toBeInTheDocument();
  });

  // 2. Owner badge renders
  it('renders Primary Owner badge for project creator with is_owner=true', () => {
    render(<ProjectMemberCard member={mockOwnerMember} />);

    expect(screen.getByText('Aarav Sharma')).toBeInTheDocument();
    expect(screen.getByText('Primary Owner')).toBeInTheDocument();
    expect(screen.getByText('50.0%')).toBeInTheDocument();
  });

  // 3. Project-member roles render correctly
  it('renders Faculty Mentor badge for FACULTY_MENTOR role', () => {
    render(<ProjectMemberCard member={mockMentorMember} />);

    expect(screen.getByText('Dr. Rajesh Verma')).toBeInTheDocument();
    expect(screen.getByText('Faculty Mentor')).toBeInTheDocument();
    expect(screen.getByText('10.0%')).toBeInTheDocument();
  });

  // 4. Copy email button in member card
  it('allows copying member email to clipboard', async () => {
    render(<ProjectMemberCard member={mockContributorMember} />);

    const copyBtn = screen.getByLabelText('Copy member email');
    fireEvent.click(copyBtn);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('contributor@sih2026.edu');
  });

  // 5. Team empty state renders
  it('renders empty state when members list is empty', () => {
    const auth = createMockAuthContext();
    render(
      <AuthContext.Provider value={auth}>
        <ProjectTeamSection
          projectId="PRJ-202609-A8F92"
          project={mockProject}
          members={[]}
          onMemberAdded={vi.fn()}
        />
      </AuthContext.Provider>
    );

    expect(screen.getByText(/No Additional Team Members Yet/i)).toBeInTheDocument();
    expect(screen.getByText(/Primary creator is Aarav Sharma/i)).toBeInTheDocument();
  });

  // 6. Add Member button visible for owner, hidden for non-owner
  it('shows Add Member button for owner and hides for non-owner student', () => {
    const ownerAuth = createMockAuthContext();
    const { rerender } = render(
      <AuthContext.Provider value={ownerAuth}>
        <ProjectTeamSection
          projectId="PRJ-202609-A8F92"
          project={mockProject}
          members={[mockOwnerMember]}
          onMemberAdded={vi.fn()}
        />
      </AuthContext.Provider>
    );

    expect(screen.getByRole('button', { name: /Add Member/i })).toBeInTheDocument();

    // Rerender as unrelated student
    const guestAuth = createMockAuthContext({
      user: {
        public_id: 'USR-202609-GUEST1',
        email: 'guest@sih2026.edu',
        full_name: 'Guest Student',
        role: 'STUDENT',
        institution_id: 'INST-OTHER',
        department: 'Math',
      },
    });

    rerender(
      <AuthContext.Provider value={guestAuth}>
        <ProjectTeamSection
          projectId="PRJ-202609-A8F92"
          project={mockProject}
          members={[mockOwnerMember]}
          onMemberAdded={vi.fn()}
        />
      </AuthContext.Provider>
    );

    expect(screen.queryByRole('button', { name: /Add Member/i })).not.toBeInTheDocument();
  });

  // 7. Add Member modal opens, required validation works
  it('opens AddMemberModal and enforces required identifier validation', async () => {
    const handleSuccess = vi.fn();
    const handleClose = vi.fn();

    render(
      <AddMemberModal
        projectId="PRJ-202609-A8F92"
        isOpen={true}
        onClose={handleClose}
        onSuccess={handleSuccess}
      />
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Add Project Team Member')).toBeInTheDocument();

    // Click submit without entering identifier
    const submitBtn = screen.getByRole('button', { name: /Add Member/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Please provide a User Public ID \(USR-YYYYMM-XXXXX\) or Email address/i)
    ).toBeInTheDocument();
    expect(projectService.addMember).not.toHaveBeenCalled();
  });

  // 8. Client-side contribution percentage validation (<0 or >100)
  it('rejects invalid contribution percentage client-side', async () => {
    render(
      <AddMemberModal
        projectId="PRJ-202609-A8F92"
        isOpen={true}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    const inputId = screen.getByPlaceholderText(/e\.g\. USR-202609-8F29A or student@sih2026\.edu/i);
    const inputPercent = screen.getByPlaceholderText(/e\.g\. 25\.5/i);

    fireEvent.change(inputId, { target: { value: 'student@sih2026.edu' } });
    fireEvent.change(inputPercent, { target: { value: '150' } });

    const submitBtn = screen.getByRole('button', { name: /Add Member/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Contribution percentage must be a number between 0\.00 and 100\.00%/i)
    ).toBeInTheDocument();
    expect(projectService.addMember).not.toHaveBeenCalled();
  });

  // 9. Adding member by Email with CONTRIBUTOR role
  it('submits member addition by email with CONTRIBUTOR role', async () => {
    vi.mocked(projectService.addMember).mockResolvedValueOnce(mockContributorMember);
    const handleSuccess = vi.fn();
    const handleClose = vi.fn();

    render(
      <AddMemberModal
        projectId="PRJ-202609-A8F92"
        isOpen={true}
        onClose={handleClose}
        onSuccess={handleSuccess}
      />
    );

    const inputId = screen.getByPlaceholderText(/e\.g\. USR-202609-8F29A or student@sih2026\.edu/i);
    const inputPercent = screen.getByPlaceholderText(/e\.g\. 25\.5/i);

    fireEvent.change(inputId, { target: { value: 'contributor@sih2026.edu' } });
    fireEvent.change(inputPercent, { target: { value: '25.5' } });

    const submitBtn = screen.getByRole('button', { name: /Add Member/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(projectService.addMember).toHaveBeenCalledWith('PRJ-202609-A8F92', {
        email: 'contributor@sih2026.edu',
        role_in_project: 'CONTRIBUTOR',
        contribution_percentage: 25.5,
      });
      expect(handleSuccess).toHaveBeenCalledWith(mockContributorMember);
      expect(handleClose).toHaveBeenCalled();
    });
  });

  // 10. Adding member by user_public_id with FACULTY_MENTOR role
  it('submits member addition by user_public_id with FACULTY_MENTOR role', async () => {
    vi.mocked(projectService.addMember).mockResolvedValueOnce(mockMentorMember);
    const handleSuccess = vi.fn();
    const handleClose = vi.fn();

    render(
      <AddMemberModal
        projectId="PRJ-202609-A8F92"
        isOpen={true}
        onClose={handleClose}
        onSuccess={handleSuccess}
      />
    );

    const inputId = screen.getByPlaceholderText(/e\.g\. USR-202609-8F29A or student@sih2026\.edu/i);
    const mentorRoleBtn = screen.getByRole('button', { name: /Faculty Mentor/i });
    const inputPercent = screen.getByPlaceholderText(/e\.g\. 25\.5/i);

    fireEvent.change(inputId, { target: { value: 'USR-202609-MENTOR1' } });
    fireEvent.click(mentorRoleBtn);
    fireEvent.change(inputPercent, { target: { value: '10' } });

    const submitBtn = screen.getByRole('button', { name: /Add Member/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(projectService.addMember).toHaveBeenCalledWith('PRJ-202609-A8F92', {
        user_public_id: 'USR-202609-MENTOR1',
        role_in_project: 'FACULTY_MENTOR',
        contribution_percentage: 10,
      });
      expect(handleSuccess).toHaveBeenCalledWith(mockMentorMember);
    });
  });

  // 11. Adding member with LEAD role
  it('submits member addition with LEAD role', async () => {
    const mockCoLead: ProjectMemberItem = {
      ...mockContributorMember,
      role_in_project: 'LEAD',
    };
    vi.mocked(projectService.addMember).mockResolvedValueOnce(mockCoLead);

    render(
      <AddMemberModal
        projectId="PRJ-202609-A8F92"
        isOpen={true}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    const inputId = screen.getByPlaceholderText(/e\.g\. USR-202609-8F29A or student@sih2026\.edu/i);
    const leadRoleBtn = screen.getByRole('button', { name: /Co-Lead/i });

    fireEvent.change(inputId, { target: { value: 'USR-202609-COLEAD1' } });
    fireEvent.click(leadRoleBtn);

    const submitBtn = screen.getByRole('button', { name: /Add Member/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(projectService.addMember).toHaveBeenCalledWith('PRJ-202609-A8F92', {
        user_public_id: 'USR-202609-COLEAD1',
        role_in_project: 'LEAD',
        contribution_percentage: 0,
      });
    });
  });

  // 12. Duplicate submit prevention (loading state disables submit button)
  it('disables submit button while loading to prevent duplicate requests', async () => {
    let resolvePromise: (val: ProjectMemberItem) => void = () => {};
    vi.mocked(projectService.addMember).mockReturnValueOnce(
      new Promise((res) => {
        resolvePromise = res;
      })
    );

    render(
      <AddMemberModal
        projectId="PRJ-202609-A8F92"
        isOpen={true}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    const inputId = screen.getByPlaceholderText(/e\.g\. USR-202609-8F29A or student@sih2026\.edu/i);
    fireEvent.change(inputId, { target: { value: 'student@sih2026.edu' } });

    const submitBtn = screen.getByRole('button', { name: /Add Member/i });
    fireEvent.click(submitBtn);

    expect(screen.getByText('Adding Member...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Adding Member\.\.\./i })).toBeDisabled();

    // Resolve promise
    resolvePromise(mockContributorMember);
  });

  // 13. Error handling: 401 Unauthorized
  it('handles 401 Unauthorized error with ErrorBanner', async () => {
    vi.mocked(projectService.addMember).mockRejectedValueOnce({
      response: {
        status: 401,
        data: {
          success: false,
          error: {
            code: 'UNAUTHORIZED',
            message: 'Authentication credentials missing or invalid.',
          },
        },
      },
    });

    render(
      <AddMemberModal
        projectId="PRJ-202609-A8F92"
        isOpen={true}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    const inputId = screen.getByPlaceholderText(/e\.g\. USR-202609-8F29A or student@sih2026\.edu/i);
    fireEvent.change(inputId, { target: { value: 'student@sih2026.edu' } });

    const submitBtn = screen.getByRole('button', { name: /Add Member/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText('Authentication credentials missing or invalid.')
    ).toBeInTheDocument();
  });

  // 14. Error handling: 403 Forbidden
  it('handles 403 Forbidden error when non-lead attempts to add a member', async () => {
    vi.mocked(projectService.addMember).mockRejectedValueOnce({
      response: {
        status: 403,
        data: {
          success: false,
          error: {
            code: 'FORBIDDEN',
            message: 'Only the project lead or owner is authorized to add team members.',
          },
        },
      },
    });

    render(
      <AddMemberModal
        projectId="PRJ-202609-A8F92"
        isOpen={true}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    const inputId = screen.getByPlaceholderText(/e\.g\. USR-202609-8F29A or student@sih2026\.edu/i);
    fireEvent.change(inputId, { target: { value: 'student@sih2026.edu' } });

    const submitBtn = screen.getByRole('button', { name: /Add Member/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText('Only the project lead or owner is authorized to add team members.')
    ).toBeInTheDocument();
  });

  // 15. Error handling: 404 User Not Found
  it('handles 404 User Not Found error when target user does not exist', async () => {
    vi.mocked(projectService.addMember).mockRejectedValueOnce({
      response: {
        status: 404,
        data: {
          success: false,
          error: {
            code: 'USER_NOT_FOUND',
            message: 'The specified user does not exist.',
          },
        },
      },
    });

    render(
      <AddMemberModal
        projectId="PRJ-202609-A8F92"
        isOpen={true}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    const inputId = screen.getByPlaceholderText(/e\.g\. USR-202609-8F29A or student@sih2026\.edu/i);
    fireEvent.change(inputId, { target: { value: 'nonexistent@sih2026.edu' } });

    const submitBtn = screen.getByRole('button', { name: /Add Member/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText('The specified user does not exist.')
    ).toBeInTheDocument();
  });

  // 16. Error handling: 409 Conflict (Duplicate Member)
  it('handles 409 Conflict error when member is already added', async () => {
    vi.mocked(projectService.addMember).mockRejectedValueOnce({
      response: {
        status: 409,
        data: {
          success: false,
          error: {
            code: 'MEMBER_ALREADY_EXISTS',
            message: "User 'Diya Patel' is already a member of this project.",
          },
        },
      },
    });

    render(
      <AddMemberModal
        projectId="PRJ-202609-A8F92"
        isOpen={true}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    const inputId = screen.getByPlaceholderText(/e\.g\. USR-202609-8F29A or student@sih2026\.edu/i);
    fireEvent.change(inputId, { target: { value: 'contributor@sih2026.edu' } });

    const submitBtn = screen.getByRole('button', { name: /Add Member/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText("User 'Diya Patel' is already a member of this project.")
    ).toBeInTheDocument();
  });

  // 17. Error handling: 422 Unprocessable Entity
  it('handles 422 Validation Error', async () => {
    vi.mocked(projectService.addMember).mockRejectedValueOnce({
      response: {
        status: 422,
        data: {
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: "Validation failure in request payload.",
            details: [
              { field: 'contribution_percentage', message: 'Input should be less than or equal to 100' }
            ]
          },
        },
      },
    });

    render(
      <AddMemberModal
        projectId="PRJ-202609-A8F92"
        isOpen={true}
        onClose={vi.fn()}
        onSuccess={vi.fn()}
      />
    );

    const inputId = screen.getByPlaceholderText(/e\.g\. USR-202609-8F29A or student@sih2026\.edu/i);
    fireEvent.change(inputId, { target: { value: 'contributor@sih2026.edu' } });

    const submitBtn = screen.getByRole('button', { name: /Add Member/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText(/Validation failure in request payload/i)
    ).toBeInTheDocument();
  });

  // 18. Full integration with ProjectDetailPage
  it('loads project details, lists existing members, and allows adding a member dynamically', async () => {
    vi.mocked(projectService.getProject).mockResolvedValueOnce(mockProject);
    vi.mocked(projectService.listMembers).mockResolvedValueOnce([mockOwnerMember]);
    vi.mocked(projectService.listVersions).mockResolvedValueOnce([]);
    vi.mocked(projectService.addMember).mockResolvedValueOnce(mockContributorMember);

    const auth = createMockAuthContext();

    render(
      <AuthContext.Provider value={auth}>
        <MemoryRouter initialEntries={['/projects/PRJ-202609-A8F92']}>
          <Routes>
            <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );

    // Verify initial owner member loaded
    expect((await screen.findAllByText('Aarav Sharma')).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Primary Owner')).toBeInTheDocument();

    // Click Add Member
    const addMemberBtn = screen.getByRole('button', { name: /Add Member/i });
    fireEvent.click(addMemberBtn);

    // Modal opens
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    const inputId = screen.getByPlaceholderText(/e\.g\. USR-202609-8F29A or student@sih2026\.edu/i);
    fireEvent.change(inputId, { target: { value: 'contributor@sih2026.edu' } });

    const modalSubmitBtn = screen.getAllByRole('button', { name: /Add Member/i })[1];
    fireEvent.click(modalSubmitBtn);

    // New member should now be in the UI
    expect(await screen.findByText('Diya Patel')).toBeInTheDocument();
    expect(screen.getByText('contributor@sih2026.edu')).toBeInTheDocument();
  });
});
