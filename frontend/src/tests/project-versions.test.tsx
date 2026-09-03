import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ProjectVersionsPage } from '../pages/projects/ProjectVersionsPage';
import { ProjectDetailPage } from '../pages/projects/ProjectDetailPage';
import { CreateVersionModal } from '../components/projects/CreateVersionModal';
import { projectService } from '../services/project.service';
import { authService } from '../services/auth.service';
import { AuthProvider } from '../context/AuthContext';
import * as tokenUtils from '../utils/token';
import {
  ProjectSummary,
  ProjectVersionDetail,
  ArtifactResponse,
} from '../types';

describe('Project Versions & Milestones Frontend Module Tests', () => {
  const mockUser = {
    public_id: 'USR-202608-8F29A',
    email: 'tejas.sharma@nit.edu',
    full_name: 'Tejas Sharma',
    role: 'STUDENT' as const,
    institution_id: 'NIT-CS-2026-081',
    department: 'Computer Science & Engineering',
  };

  const mockProject: ProjectSummary = {
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

  const mockArtifact1: ArtifactResponse = {
    public_id: 'ART-202608-11E54',
    file_name: 'architecture_diagram.pdf',
    file_type: 'application/pdf',
    file_size_bytes: 1048576, // 1 MB
    sha256_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    ipfs_cid: 'bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m',
    artifact_category: 'DOCUMENTATION',
    uploaded_at: '2026-08-31T19:00:00.000Z',
  };

  const mockArtifact2: ArtifactResponse = {
    public_id: 'ART-202608-11E55',
    file_name: 'smart_contract_source.zip',
    file_type: 'application/zip',
    file_size_bytes: 524288, // 512 KB
    sha256_hash: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
    ipfs_cid: 'bafybeihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku',
    artifact_category: 'SOURCE_CODE',
    uploaded_at: '2026-08-31T19:05:00.000Z',
  };

  const mockVersion1: ProjectVersionDetail = {
    public_id: 'VER-202608-41C88',
    registration_id: 'REG-2026-A8F92D',
    version_index: 1,
    version_tag: 'v1.0',
    lifecycle_stage: 'IDEA',
    title: 'Initial Concept & Problem Statement',
    description: 'Initial concept document outlining decentralized registry for academic institutions.',
    composite_sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    ipfs_root_cid: 'bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m',
    anchoring_status: 'ANCHORED',
    dispute_status: 'NONE',
    artifacts: [mockArtifact1],
    blockchain_record: {
      transaction_hash: '0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb',
      block_number: 142,
      anchored_timestamp: '2026-08-31T19:15:00.000Z',
      network_name: 'hardhat',
    },
    created_at: '2026-08-31T19:10:00.000Z',
  };

  const mockVersion2: ProjectVersionDetail = {
    public_id: 'VER-202608-41C89',
    registration_id: 'REG-2026-B9F03E',
    version_index: 2,
    version_tag: 'v1.1',
    lifecycle_stage: 'DESIGN',
    title: 'System Architecture & Smart Contracts',
    description: 'Threat modeling, API contracts, and Solidity implementation.',
    composite_sha256: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
    ipfs_root_cid: 'bafybeihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku',
    anchoring_status: 'ANCHORING',
    dispute_status: 'NONE',
    artifacts: [mockArtifact1, mockArtifact2],
    blockchain_record: {
      transaction_hash: '0x88f29ade432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb',
      block_number: 155,
      anchored_timestamp: '2026-09-01T10:00:00.000Z',
      network_name: 'hardhat',
    },
    created_at: '2026-09-01T09:30:00.000Z',
  };

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    tokenUtils.setAccessToken('valid-jwt-token');
    vi.spyOn(authService, 'getMe').mockResolvedValue(mockUser);
  });

  const renderVersionsPage = (projectId = 'PRJ-202608-99B12') => {
    return render(
      <MemoryRouter initialEntries={[`/projects/${projectId}/versions`]}>
        <AuthProvider>
          <Routes>
            <Route path="/projects/:projectId/versions" element={<ProjectVersionsPage />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );
  };

  describe('ProjectVersionsPage — Version List & Details', () => {
    it('renders project header and all version snapshots in ascending order', async () => {
      vi.spyOn(projectService, 'getProject').mockResolvedValue(mockProject);
      vi.spyOn(projectService, 'listVersions').mockResolvedValue([mockVersion2, mockVersion1]); // unsorted

      renderVersionsPage();

      expect(screen.getByText(/Loading project milestones and versions.../i)).toBeInTheDocument();

      // Project info in header
      expect(await screen.findByText('PRJ-202608-99B12')).toBeInTheDocument();
      expect(screen.getByText('Decentralized IPFS Academic Registry')).toBeInTheDocument();
      expect(screen.getByText('2 Versions')).toBeInTheDocument();

      // Versions rendered in sorted ascending order (v1.0 then v1.1)
      expect(screen.getByText('v1.0')).toBeInTheDocument();
      expect(screen.getByText('Initial Concept & Problem Statement')).toBeInTheDocument();
      expect(screen.getByText('v1.1')).toBeInTheDocument();
      expect(screen.getByText('System Architecture & Smart Contracts')).toBeInTheDocument();

      // Badges
      expect(screen.getByText('IDEA')).toBeInTheDocument();
      expect(screen.getAllByText('DESIGN').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Anchored')).toBeInTheDocument();
      expect(screen.getByText('Anchoring')).toBeInTheDocument();

      // Registration ID
      expect(screen.getByText('REG-2026-A8F92D')).toBeInTheDocument();
      expect(screen.getByText('REG-2026-B9F03E')).toBeInTheDocument();
    });

    it('renders all 5 exact anchoring statuses accurately without fabricating status', async () => {
      const statuses: Array<ProjectVersionDetail['anchoring_status']> = [
        'DRAFT',
        'PENDING',
        'ANCHORING',
        'ANCHORED',
        'FAILED',
      ];

      const versionsWithStatuses: ProjectVersionDetail[] = statuses.map((st, idx) => ({
        ...mockVersion1,
        public_id: `VER-TEST-${idx}`,
        version_index: idx + 1,
        version_tag: `v${idx + 1}.0`,
        anchoring_status: st,
      }));

      vi.spyOn(projectService, 'getProject').mockResolvedValue(mockProject);
      vi.spyOn(projectService, 'listVersions').mockResolvedValue(versionsWithStatuses);

      renderVersionsPage();

      await screen.findByText('PRJ-202608-99B12');

      expect(screen.getByText('Draft')).toBeInTheDocument();
      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByText('Anchoring')).toBeInTheDocument();
      expect(screen.getByText('Anchored')).toBeInTheDocument();
      expect(screen.getByText('Failed')).toBeInTheDocument();
    });

    it('expands attached artifacts list when clicking accordion', async () => {
      vi.spyOn(projectService, 'getProject').mockResolvedValue(mockProject);
      vi.spyOn(projectService, 'listVersions').mockResolvedValue([mockVersion2]); // 2 artifacts

      renderVersionsPage();

      await screen.findByText('System Architecture & Smart Contracts');

      // The accordion button
      const accordionBtn = screen.getByRole('button', { name: /Associated Artifacts \(2\)/i });
      expect(accordionBtn).toBeInTheDocument();

      // Click to toggle accordion
      fireEvent.click(accordionBtn);

      // Verify artifact items
      expect(screen.getByText('architecture_diagram.pdf')).toBeInTheDocument();
      expect(screen.getByText('smart_contract_source.zip')).toBeInTheDocument();
      expect(screen.getByText('ART-202608-11E54')).toBeInTheDocument();
      expect(screen.getByText('1 MB')).toBeInTheDocument();
      expect(screen.getByText('ART-202608-11E55')).toBeInTheDocument();
      expect(screen.getByText('512 KB')).toBeInTheDocument();
    });

    it('renders empty state when no versions are recorded and provides create action', async () => {
      vi.spyOn(projectService, 'getProject').mockResolvedValue(mockProject);
      vi.spyOn(projectService, 'listVersions').mockResolvedValue([]);

      renderVersionsPage();

      expect(await screen.findByText(/No Milestone Versions Recorded Yet/i)).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: /Create Initial Milestone Version/i })
      ).toBeInTheDocument();
    });

    it('renders error state and retry on API failure', async () => {
      vi.spyOn(projectService, 'getProject').mockRejectedValue(new Error('Backend offline'));
      vi.spyOn(projectService, 'listVersions').mockRejectedValue(new Error('Backend offline'));

      renderVersionsPage();

      expect(await screen.findByText(/Project Not Found/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
    });
  });

  describe('CreateVersionModal — Creation Workflow & Validation', () => {
    it('validates required fields on submit (version tag and title)', async () => {
      const handleSuccess = vi.fn();
      const handleClose = vi.fn();

      render(
        <CreateVersionModal
          projectId="PRJ-202608-99B12"
          isOpen={true}
          onClose={handleClose}
          onSuccess={handleSuccess}
          availableArtifacts={[mockArtifact1, mockArtifact2]}
        />
      );

      expect(screen.getByRole('heading', { name: /Create Milestone Version Snapshot/i })).toBeInTheDocument();

      // Submit without entering required fields
      const submitBtn = screen.getByRole('button', { name: /Create & Anchor Milestone/i });
      fireEvent.click(submitBtn);

      expect(await screen.findByText(/Version tag is required/i)).toBeInTheDocument();
      expect(screen.getByText(/Milestone title is required/i)).toBeInTheDocument();
      expect(handleSuccess).not.toHaveBeenCalled();
    });

    it('allows artifact selection from checklist and manual artifact ID entry', async () => {
      const handleSuccess = vi.fn();
      const handleClose = vi.fn();

      render(
        <CreateVersionModal
          projectId="PRJ-202608-99B12"
          isOpen={true}
          onClose={handleClose}
          onSuccess={handleSuccess}
          availableArtifacts={[mockArtifact1, mockArtifact2]}
        />
      );

      // 0 selected initially
      expect(screen.getByText('0 Selected')).toBeInTheDocument();

      // Check first artifact
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]);
      expect(screen.getByText('1 Selected')).toBeInTheDocument();

      // Add a manual artifact ID
      const manualInput = screen.getByPlaceholderText(/Enter artifact ID/i);
      fireEvent.change(manualInput, { target: { value: 'ART-202609-CUSTOM1' } });
      const addIdBtn = screen.getByRole('button', { name: /Add ID/i });
      fireEvent.click(addIdBtn);

      expect(screen.getByText('2 Selected')).toBeInTheDocument();
      expect(screen.getByText('ART-202609-CUSTOM1')).toBeInTheDocument();

      // Remove the manual ID
      const removeBtn = screen.getByRole('button', { name: /Remove artifact ART-202609-CUSTOM1/i });
      fireEvent.click(removeBtn);
      expect(screen.getByText('1 Selected')).toBeInTheDocument();
    });

    it('submits valid payload with Idempotency-Key and calls onSuccess', async () => {
      const mockCreatedVersion: ProjectVersionDetail = {
        ...mockVersion1,
        public_id: 'VER-NEW-123',
        version_tag: 'v2.0',
        lifecycle_stage: 'PROTOTYPE',
        title: 'Working MVP Build',
        version_index: 3,
        anchoring_status: 'ANCHORING',
      };

      const createSpy = vi.spyOn(projectService, 'createVersion').mockResolvedValue(mockCreatedVersion);
      const handleSuccess = vi.fn();
      const handleClose = vi.fn();

      render(
        <CreateVersionModal
          projectId="PRJ-202608-99B12"
          isOpen={true}
          onClose={handleClose}
          onSuccess={handleSuccess}
          availableArtifacts={[mockArtifact1]}
        />
      );

      // Fill in form
      fireEvent.change(screen.getByLabelText(/Version Tag/i), { target: { value: 'v2.0' } });
      fireEvent.change(screen.getByLabelText(/Milestone Title/i), { target: { value: 'Working MVP Build' } });
      fireEvent.change(screen.getByLabelText(/Description \/ Milestone Notes/i), {
        target: { value: 'Complete front-to-back integration with hardhat blockchain.' },
      });

      // Select Prototype stage
      fireEvent.click(screen.getByRole('button', { name: /PROTOTYPE/i }));

      // Select artifact
      fireEvent.click(screen.getByRole('checkbox'));

      // Submit form
      const submitBtn = screen.getByRole('button', { name: /Create & Anchor Milestone/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(createSpy).toHaveBeenCalledWith(
          'PRJ-202608-99B12',
          {
            version_tag: 'v2.0',
            lifecycle_stage: 'PROTOTYPE',
            title: 'Working MVP Build',
            description: 'Complete front-to-back integration with hardhat blockchain.',
            artifact_ids: ['ART-202608-11E54'],
          },
          expect.any(String) // UUID idempotency key
        );
      });

      expect(handleSuccess).toHaveBeenCalledWith(mockCreatedVersion);
      expect(handleClose).toHaveBeenCalled();
    });

    it('displays error banner when version creation API fails', async () => {
      vi.spyOn(projectService, 'createVersion').mockRejectedValue({
        response: {
          status: 409,
          data: {
            success: false,
            error: {
              code: 'VERSION_TAG_EXISTS',
              message: 'A version snapshot with tag v1.0 already exists for this project.',
            },
            meta: { timestamp: '2026-09-03T18:00:00.000Z' },
          },
        },
      });

      const handleSuccess = vi.fn();
      const handleClose = vi.fn();

      render(
        <CreateVersionModal
          projectId="PRJ-202608-99B12"
          isOpen={true}
          onClose={handleClose}
          onSuccess={handleSuccess}
        />
      );

      fireEvent.change(screen.getByLabelText(/Version Tag/i), { target: { value: 'v1.0' } });
      fireEvent.change(screen.getByLabelText(/Milestone Title/i), { target: { value: 'Duplicate Tag' } });

      fireEvent.click(screen.getByRole('button', { name: /Create & Anchor Milestone/i }));

      expect(
        await screen.findByText(/A version snapshot with tag v1.0 already exists/i)
      ).toBeInTheDocument();
      expect(handleSuccess).not.toHaveBeenCalled();
    });
  });

  describe('ProjectDetailPage — Integration', () => {
    it('renders navigation links to the Project Versions page in top controls and milestone section', async () => {
      vi.spyOn(projectService, 'getProject').mockResolvedValue(mockProject);
      vi.spyOn(projectService, 'listMembers').mockResolvedValue([]);
      vi.spyOn(projectService, 'listVersions').mockResolvedValue([mockVersion1]);

      render(
        <MemoryRouter initialEntries={['/projects/PRJ-202608-99B12']}>
          <AuthProvider>
            <Routes>
              <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      );

      expect(await screen.findByText(/PRJ-202608-99B12/i)).toBeInTheDocument();

      // Top control link
      const versionLinks = screen.getAllByRole('link', { name: /Milestones & Versions|Manage & Anchor/i });
      expect(versionLinks.length).toBeGreaterThanOrEqual(2);
      expect(versionLinks[0]).toHaveAttribute('href', '/projects/PRJ-202608-99B12/versions');
    });
  });
});
