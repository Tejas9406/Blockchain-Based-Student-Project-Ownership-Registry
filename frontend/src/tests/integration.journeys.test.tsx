import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { AppRoutes } from '../app/router';
import { authService } from '../services/auth.service';
import { projectService } from '../services/project.service';
import { verificationService } from '../services/verification.service';
import { disputeService } from '../services/dispute.service';
import { certificateService } from '../services/certificate.service';
import * as tokenUtils from '../utils/token';
import {
  ProjectSummary,
  ProjectMemberItem,
  ProjectVersionDetail,
  VerificationResponseData,
  DisputeDetailResponse,
  CertificateMetadataData,
  UserSummaryResponse,
} from '../types';

// Mock clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockImplementation(() => Promise.resolve()),
  },
});

// Mock URL object methods
window.URL.createObjectURL = vi.fn().mockReturnValue('blob:http://localhost/mock-cert.pdf');
window.URL.revokeObjectURL = vi.fn();

// Mock data fixtures
const mockStudentUser: UserSummaryResponse = {
  public_id: 'USR-202608-8F29A',
  email: 'student@institution.edu',
  full_name: 'Tejas Sharma',
  role: 'STUDENT',
  institution_id: 'NIT-2026-001',
  department: 'Computer Science & Engineering',
};

const mockAdminUser: UserSummaryResponse = {
  public_id: 'USR-202608-ADMIN',
  email: 'admin@institution.edu',
  full_name: 'Dr. Administrator',
  role: 'ADMIN',
  institution_id: 'NIT-ADMIN-01',
  department: 'Administration',
};

const mockProject: ProjectSummary = {
  public_id: 'PRJ-202608-99B12',
  slug: 'decentralized-ipfs-academic-registry',
  title: 'Decentralized IPFS Academic Registry',
  abstract: 'A tamper-proof system for registering student research and projects.',
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

const mockMember: ProjectMemberItem = {
  user: {
    public_id: 'USR-202608-8F29A',
    email: 'student@institution.edu',
    full_name: 'Tejas Sharma',
    institution_id: 'NIT-2026-001',
    institution_name: 'National Institute of Technology',
    department: 'Computer Science & Engineering',
    role: 'STUDENT',
    is_verified: true,
    created_at: '2026-08-31T18:50:00.000Z',
  },
  role_in_project: 'LEAD',
  contribution_percentage: 100,
  is_owner: true,
  joined_at: '2026-08-31T18:50:00.000Z',
};

const mockVersion: ProjectVersionDetail = {
  public_id: 'VER-202608-41C88',
  registration_id: 'REG-2026-A8F92D',
  version_index: 1,
  version_tag: 'v1.0',
  lifecycle_stage: 'DESIGN',
  title: 'System Architecture & Threat Model',
  description: 'Initial architectural specifications.',
  composite_sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
  ipfs_root_cid: 'bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m',
  anchoring_status: 'ANCHORED',
  dispute_status: 'NONE',
  artifacts: [
    {
      public_id: 'ART-202608-11E54',
      file_name: 'architecture_diagram.pdf',
      file_type: 'application/pdf',
      file_size_bytes: 2048576,
      sha256_hash: '3a4b5c6d7e8f3a4b5c6d7e8f3a4b5c6d7e8f3a4b5c6d7e8f3a4b5c6d7e8f3a4b',
      ipfs_cid: 'bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m',
      artifact_category: 'DESIGN_SPEC',
      uploaded_at: '2026-08-31T18:50:00.000Z',
    },
  ],
  blockchain_record: {
    transaction_hash: '0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb',
    block_number: 142981,
    anchored_timestamp: '2026-08-31T18:50:00.000Z',
    smart_contract_address: '0x5FbDB2315678afecb367f032d93F642f64180aa3',
    author_wallet: '0x70997970C51812dc3A010C7d01b50e0d17dc79C8',
    network_name: 'sepolia',
  },
  created_at: '2026-08-31T18:50:00.000Z',
};

const mockVerification: VerificationResponseData = {
  is_valid: true,
  registration_id: 'REG-2026-A8F92D',
  verification_method: 'REGISTRATION_ID',
  anchoring_status: 'ANCHORED',
  project: {
    public_id: 'PRJ-202608-99B12',
    title: 'Decentralized IPFS Academic Registry',
    department: 'Computer Science & Engineering',
    institution_name: 'National Institute of Technology',
  },
  version: {
    version_tag: 'v1.0',
    lifecycle_stage: 'DESIGN',
    composite_sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    ipfs_root_cid: 'bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m',
  },
  blockchain_proof: {
    transaction_hash: '0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb',
    block_number: 142981,
    block_timestamp: '2026-08-31T18:50:00.000Z',
    smart_contract_address: '0x5FbDB2315678afecb367f032d93F642f64180aa3',
    author_wallet: '0x70997970C51812dc3A010C7d01b50e0d17dc79C8',
    network_name: 'sepolia',
    dispute_status: 'NONE',
    match_confirmed: true,
  },
};

const mockDispute: DisputeDetailResponse = {
  public_id: 'DSP-202609-A8F92',
  project_public_id: 'PRJ-202608-99B12',
  project_title: 'Decentralized IPFS Academic Registry',
  registration_id: 'REG-2026-A8F92D',
  dispute_type: 'PLAGIARISM',
  claim_description: 'Architecture diagram copied from our research paper published in 2024.',
  evidence_url: 'bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m',
  status: 'OPEN',
  transaction_hash: '0x1111111111111111111111111111111111111111111111111111111111111111',
  claimant: {
    public_id: 'USR-202608-CLAIMANT',
    full_name: 'Prior Art Author',
    institution_id: 'NIT-2024',
  },
  created_at: '2026-09-01T12:00:00.000Z',
};

const mockCertificate: CertificateMetadataData = {
  registration_id: 'REG-2026-A8F92D',
  project_title: 'Decentralized IPFS Academic Registry',
  version_tag: 'v1.0',
  lifecycle_stage: 'DESIGN',
  authors: ['Tejas Sharma'],
  institution: 'National Institute of Technology',
  department: 'Computer Science & Engineering',
  anchored_timestamp: '2026-08-31T18:50:00.000Z',
  transaction_hash: '0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb',
  block_number: 142981,
  composite_sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
  ipfs_root_cid: 'bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m',
  verification_url: 'https://registry.sih2026.edu/verify/REG-2026-A8F92D',
  qr_code_svg_url: 'https://registry.sih2026.edu/api/v1/certificates/REG-2026-A8F92D/qr.svg',
  pdf_download_url: 'https://registry.sih2026.edu/api/v1/certificates/REG-2026-A8F92D/download',
  dispute_status: 'NONE',
};

describe('STEP 2.12 Production Integration Journeys', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    tokenUtils.clearTokens();
    vi.spyOn(authService, 'getMe').mockRejectedValue(new Error('Unauthenticated'));
  });

  const setupAuth = (user: UserSummaryResponse = mockStudentUser) => {
    tokenUtils.setAccessToken('mock-valid-token');
    vi.spyOn(authService, 'getMe').mockResolvedValue(user);
  };

  it('Journey 1: Login → Dashboard interactive authentication flow', async () => {
    vi.spyOn(authService, 'login').mockResolvedValueOnce({
      access_token: 'new-token-123',
      refresh_token: 'refresh-token-123',
      token_type: 'bearer',
      expires_in: 3600,
      user: mockStudentUser,
    });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument();

    const emailInput = screen.getByLabelText(/Email Address/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const submitBtn = screen.getByRole('button', { name: /Sign In/i });

    fireEvent.change(emailInput, { target: { value: 'student@institution.edu' } });
    fireEvent.change(passwordInput, { target: { value: 'securepassword123' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith({
        email: 'student@institution.edu',
        password: 'securepassword123',
      });
    });

    expect(await screen.findByText(/Welcome back,/i)).toBeInTheDocument();
    expect(screen.getAllByText('Tejas Sharma').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('STUDENT').length).toBeGreaterThanOrEqual(1);
  });

  it('Journey 2 & 3: Dashboard → Projects → Project Detail navigation flow', async () => {
    setupAuth();
    vi.spyOn(projectService, 'listProjects').mockResolvedValue({
      success: true,
      data: [mockProject],
      meta: {
        page: 1,
        page_size: 12,
        total_items: 1,
        total_pages: 1,
        has_next: false,
        has_prev: false,
        timestamp: '2026-08-31T18:50:00.000Z',
      },
    });
    vi.spyOn(projectService, 'getProject').mockResolvedValue(mockProject);
    vi.spyOn(projectService, 'listMembers').mockResolvedValue([mockMember]);
    vi.spyOn(projectService, 'listVersions').mockResolvedValue([mockVersion]);

    render(
      <MemoryRouter initialEntries={['/projects']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Academic Project Catalog')).toBeInTheDocument();
    expect(await screen.findByText('Decentralized IPFS Academic Registry')).toBeInTheDocument();

    const viewProjectLink = screen.getByRole('link', { name: /View Details/i });
    expect(viewProjectLink).toHaveAttribute('href', '/projects/PRJ-202608-99B12');
  });

  it('Journey 4, 5, 6, 7: Project Detail → Team, Artifacts, Versions, Disputes cross-links', async () => {
    setupAuth();
    vi.spyOn(projectService, 'getProject').mockResolvedValue(mockProject);
    vi.spyOn(projectService, 'listMembers').mockResolvedValue([mockMember]);
    vi.spyOn(projectService, 'listVersions').mockResolvedValue([mockVersion]);

    render(
      <MemoryRouter initialEntries={['/projects/PRJ-202608-99B12']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Decentralized IPFS Academic Registry')).toBeInTheDocument();

    // Verify links to Artifacts and Versions
    const artifactsLink = screen.getByRole('link', { name: /Manage Artifacts/i });
    expect(artifactsLink).toHaveAttribute('href', '/projects/PRJ-202608-99B12/artifacts');

    const versionsLink = screen.getByRole('link', { name: /Milestones & Versions/i });
    expect(versionsLink).toHaveAttribute('href', '/projects/PRJ-202608-99B12/versions');

    // Verify disputes link with query param
    const disputesLinks = screen.getAllByRole('link', { name: /Disputes/i });
    const projectDisputesLink = disputesLinks.find(
      (link) => link.getAttribute('href') === '/disputes?projectId=PRJ-202608-99B12'
    );
    expect(projectDisputesLink).toBeDefined();

    // Verify lead owner and team sections render
    expect(screen.getAllByText('Tejas Sharma').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Project Lead')).toBeInTheDocument();
    expect(screen.getByText('Project Team & Mentors')).toBeInTheDocument();
  });

  it('Journey 8: Project Versions → Anchored Version → Certificate Link flow', async () => {
    setupAuth();
    vi.spyOn(projectService, 'getProject').mockResolvedValue(mockProject);
    vi.spyOn(projectService, 'listVersions').mockResolvedValue([mockVersion]);

    render(
      <MemoryRouter initialEntries={['/projects/PRJ-202608-99B12/versions']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Milestone Snapshots & Anchoring History')).toBeInTheDocument();
    expect(await screen.findByText('v1.0')).toBeInTheDocument();
    expect(screen.getByText(/Anchored/i)).toBeInTheDocument();

    // Verify certificate link for anchored version
    const certLinks = screen.getAllByRole('link', { name: /Certificate/i });
    const versionCertLink = certLinks.find(
      (link) => link.getAttribute('href') === '/certificates/REG-2026-A8F92D'
    );
    expect(versionCertLink).toBeDefined();
  });

  it('Journey 9 & 10: Public Verification → Verification Detail → Certificate navigation', async () => {
    vi.spyOn(verificationService, 'verifyByRegistrationId').mockResolvedValue(mockVerification);
    vi.spyOn(certificateService, 'getCertificateMetadata').mockResolvedValue(mockCertificate);

    render(
      <MemoryRouter initialEntries={['/verify/REG-2026-A8F92D']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(verificationService.verifyByRegistrationId).toHaveBeenCalledWith('REG-2026-A8F92D');
    });

    expect(await screen.findByText(/Authoritative On-Chain EVM Blockchain Proof/i)).toBeInTheDocument();
    expect(screen.getAllByText(/REG-2026-A8F92D/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb')).toBeInTheDocument();

    // Verify link to view official certificate
    const certLinks = screen.getAllByRole('link', { name: /Certificate/i });
    const projectCertLink = certLinks.find(
      (link) => link.getAttribute('href') === '/certificates/REG-2026-A8F92D'
    );
    expect(projectCertLink).toBeDefined();
  });

  it('Journey 11 & 12: Dispute Detail — Admin Adjudication active for ADMIN, hidden for STUDENT', async () => {
    // 1. As STUDENT: Admin Adjudication panel is NOT rendered
    setupAuth(mockStudentUser);
    vi.spyOn(disputeService, 'getDispute').mockResolvedValue(mockDispute);

    const { unmount } = render(
      <MemoryRouter initialEntries={['/disputes/DSP-202609-A8F92']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Ownership & Plagiarism Dispute Dossier')).toBeInTheDocument();
    expect(screen.queryByTestId('admin-adjudication-panel')).not.toBeInTheDocument();

    unmount();

    // 2. As ADMIN: Admin Adjudication panel IS rendered with actionable decision modal
    setupAuth(mockAdminUser);
    vi.spyOn(disputeService, 'adjudicateDispute').mockResolvedValueOnce({
      ...mockDispute,
      status: 'RESOLVED',
    });

    render(
      <MemoryRouter initialEntries={['/disputes/DSP-202609-A8F92']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Ownership & Plagiarism Dispute Dossier')).toBeInTheDocument();
    expect(await screen.findByTestId('admin-adjudication-panel')).toBeInTheDocument();

    const adjudicateBtn = screen.getByRole('button', { name: /Adjudicate Claim/i });
    fireEvent.click(adjudicateBtn);

    // Modal opens with adjudication options
    expect(await screen.findByRole('heading', { name: /Adjudicate Dispute Claim/i })).toBeInTheDocument();
  });

  it('Journey 13 & 14: Certificate remains publicly accessible & handles invalid registration ID gracefully', async () => {
    // Public access works without auth
    vi.spyOn(certificateService, 'getCertificateMetadata').mockResolvedValue(mockCertificate);

    const { unmount } = render(
      <MemoryRouter initialEntries={['/certificates/REG-2026-A8F92D']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText(/Certificate of Project Ownership & Provenance/i)).toBeInTheDocument();
    expect(screen.getByText('REGISTRATION ID: REG-2026-A8F92D')).toBeInTheDocument();

    unmount();

    // Invalid ID handling
    vi.spyOn(certificateService, 'getCertificateMetadata').mockRejectedValue({
      response: {
        status: 404,
        data: {
          error: {
            code: 'REGISTRATION_NOT_FOUND',
            message: 'Registration ID not found.',
          },
        },
      },
    });

    render(
      <MemoryRouter initialEntries={['/certificates/REG-INVALID-ID']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Certificate Not Found')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Search Verification Portal/i })).toBeInTheDocument();
  });

  it('Journey 15 & 16: Protected routes reject unauthenticated users & redirect after logout', async () => {
    // Unauthenticated user attempting to access /dashboard is redirected to /login
    const { unmount } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument();

    unmount();

    // Authenticated user logs out and cannot access protected routes
    setupAuth(mockStudentUser);
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText(/Welcome back,/i)).toBeInTheDocument();

    const logoutBtn = screen.getByRole('button', { name: /Log Out/i });
    fireEvent.click(logoutBtn);

    expect(tokenUtils.getAccessToken()).toBeNull();
    expect(await screen.findByRole('heading', { name: /Welcome Back/i })).toBeInTheDocument();
  });
});
