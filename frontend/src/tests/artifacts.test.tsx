import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ProjectArtifactsPage } from '../pages/projects/ProjectArtifactsPage';
import {
  ArtifactCard,
  ArtifactList,
  ArtifactUploadForm,
  CategoryBadge,
  formatBytes,
} from '../components/artifacts';
import { artifactService } from '../services/artifact.service';
import { projectService } from '../services/project.service';
import { authService } from '../services/auth.service';
import { AuthProvider } from '../context/AuthContext';
import {
  ArtifactResponse,
  ProjectDetail,
  ProjectVersionDetail,
  UserProfileResponse,
} from '../types';

vi.mock('../services/artifact.service');
vi.mock('../services/project.service');
vi.mock('../services/auth.service');

const mockUser: UserProfileResponse = {
  public_id: 'USR-202609-00001',
  email: 'student@nit.ac.in',
  full_name: 'Student Lead',
  role: 'STUDENT',
  department: 'Computer Science & Engineering',
  institution_id: 'NIT-001',
  institution_name: 'NIT',
  created_at: '2026-09-01T00:00:00.000Z',
  is_verified: true,
};

const mockProject: ProjectDetail = {
  public_id: 'PRJ-202609-00001',
  slug: 'decentralized-registry',
  title: 'Decentralized IPFS Academic Registry',
  abstract: 'A decentralized registry using blockchain and IPFS.',
  category: 'BLOCKCHAIN',
  department: 'Computer Science & Engineering',
  academic_year: '2025-2026',
  status: 'ACTIVE',
  visibility: 'PUBLIC',
  current_lifecycle_stage: 'DESIGN',
  created_at: '2026-09-01T10:00:00Z',
  updated_at: '2026-09-02T10:00:00Z',
  owner: {
    public_id: mockUser.public_id,
    full_name: mockUser.full_name,
  },
};

const mockArtifact: ArtifactResponse = {
  public_id: 'ART-202609-11E54',
  file_name: 'architecture_v1.pdf',
  file_type: 'application/pdf',
  file_size_bytes: 1048576, // 1 MB
  sha256_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
  ipfs_cid: 'bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m',
  artifact_category: 'DESIGN_SPEC',
  uploaded_at: '2026-09-02T14:30:00Z',
};

const mockVersionWithArtifacts: ProjectVersionDetail = {
  public_id: 'VER-202609-41C88',
  registration_id: 'REG-2026-A8F92D',
  version_index: 1,
  version_tag: 'v1.0',
  lifecycle_stage: 'DESIGN',
  title: 'Architecture Spec',
  description: 'Initial architectural specification and diagrams',
  composite_sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
  ipfs_root_cid: 'bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m',
  anchoring_status: 'ANCHORED',
  dispute_status: 'NONE',
  created_at: '2026-09-02T15:00:00Z',
  artifacts: [mockArtifact],
};

function renderArtifactsPage(projectId = 'PRJ-202609-00001') {
  return render(
    <MemoryRouter initialEntries={[`/projects/${projectId}/artifacts`]}>
      <AuthProvider>
        <Routes>
          <Route
            path="/projects/:projectId/artifacts"
            element={<ProjectArtifactsPage />}
          />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('Artifacts Module Frontend Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(authService.getMe).mockResolvedValue(mockUser);
    vi.mocked(projectService.getProject).mockResolvedValue(mockProject);
    vi.mocked(projectService.listVersions).mockResolvedValue([mockVersionWithArtifacts]);
  });

  describe('formatBytes utility & Status Badges', () => {
    it('formats byte sizes correctly across units', () => {
      expect(formatBytes(0)).toBe('0 Bytes');
      expect(formatBytes(1024)).toBe('1 KB');
      expect(formatBytes(1048576)).toBe('1 MB');
      expect(formatBytes(52428800)).toBe('50 MB');
    });

    it('renders CategoryBadge with appropriate labels and classes', () => {
      const { rerender } = render(<CategoryBadge category="SOURCE_CODE" />);
      expect(screen.getByText('Source Code')).toBeInTheDocument();

      rerender(<CategoryBadge category="DOCUMENTATION" />);
      expect(screen.getByText('Documentation')).toBeInTheDocument();

      rerender(<CategoryBadge category="DESIGN_SPEC" />);
      expect(screen.getByText('Design Spec')).toBeInTheDocument();

      rerender(<CategoryBadge category="PRESENTATION" />);
      expect(screen.getByText('Presentation')).toBeInTheDocument();

      rerender(<CategoryBadge category="OTHER" />);
      expect(screen.getByText('Other File')).toBeInTheDocument();
    });
  });

  describe('ArtifactCard Component', () => {
    it('renders artifact metadata accurately', () => {
      render(<ArtifactCard artifact={mockArtifact} />);

      expect(screen.getByText('ART-202609-11E54')).toBeInTheDocument();
      expect(screen.getByText('architecture_v1.pdf')).toBeInTheDocument();
      expect(screen.getByText('Design Spec')).toBeInTheDocument();
      expect(screen.getByText('1 MB')).toBeInTheDocument();
      expect(screen.getByText('application/pdf')).toBeInTheDocument();
      expect(screen.getByText(mockArtifact.sha256_hash)).toBeInTheDocument();
      expect(screen.getByText(mockArtifact.ipfs_cid!)).toBeInTheDocument();
    });

    it('handles clipboard copy actions for ID and SHA-256 hash', async () => {
      const writeTextMock = vi.fn().mockResolvedValue(undefined);
      Object.assign(navigator, {
        clipboard: {
          writeText: writeTextMock,
        },
      });

      render(<ArtifactCard artifact={mockArtifact} />);

      const copyIdBtn = screen.getByLabelText(`Copy artifact ID ${mockArtifact.public_id}`);
      fireEvent.click(copyIdBtn);
      expect(writeTextMock).toHaveBeenCalledWith(mockArtifact.public_id);

      const copyHashBtn = screen.getByLabelText('Copy SHA-256 hash');
      fireEvent.click(copyHashBtn);
      expect(writeTextMock).toHaveBeenCalledWith(mockArtifact.sha256_hash);
    });
  });

  describe('ArtifactList Component', () => {
    it('renders empty state when no artifacts are present', () => {
      render(<ArtifactList artifacts={[]} />);
      expect(screen.getByText('No artifacts uploaded yet')).toBeInTheDocument();
    });

    it('filters artifacts by filename and category', () => {
      const artifactTwo: ArtifactResponse = {
        public_id: 'ART-202609-22B99',
        file_name: 'source_code.zip',
        file_type: 'application/zip',
        file_size_bytes: 2097152,
        sha256_hash: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        artifact_category: 'SOURCE_CODE',
        uploaded_at: '2026-09-02T16:00:00Z',
      };

      render(<ArtifactList artifacts={[mockArtifact, artifactTwo]} />);

      expect(screen.getByText('architecture_v1.pdf')).toBeInTheDocument();
      expect(screen.getByText('source_code.zip')).toBeInTheDocument();

      // Search filter
      const searchInput = screen.getByLabelText('Search artifacts');
      fireEvent.change(searchInput, { target: { value: 'source' } });

      expect(screen.queryByText('architecture_v1.pdf')).not.toBeInTheDocument();
      expect(screen.getByText('source_code.zip')).toBeInTheDocument();

      // Category filter
      fireEvent.change(searchInput, { target: { value: '' } });
      const categorySelect = screen.getByLabelText('Filter artifacts by category');
      fireEvent.change(categorySelect, { target: { value: 'DESIGN_SPEC' } });

      expect(screen.getByText('architecture_v1.pdf')).toBeInTheDocument();
      expect(screen.queryByText('source_code.zip')).not.toBeInTheDocument();
    });
  });

  describe('ArtifactUploadForm Component', () => {
    it('validates file selection before submitting', () => {
      const onUploadSuccess = vi.fn();
      render(<ArtifactUploadForm onUploadSuccess={onUploadSuccess} />);

      const submitBtn = screen.getByRole('button', { name: /Upload & Ingest Artifact/i });
      expect(submitBtn).toBeDisabled();
    });

    it('rejects 0-byte empty file with client-side validation error', () => {
      const onUploadSuccess = vi.fn();
      render(<ArtifactUploadForm onUploadSuccess={onUploadSuccess} />);

      const emptyFile = new File([''], 'empty.txt', { type: 'text/plain' });
      const fileInput = screen.getByLabelText('Select artifact file');

      fireEvent.change(fileInput, { target: { files: [emptyFile] } });

      expect(
        screen.getByText('Empty files (0 bytes) are not allowed.')
      ).toBeInTheDocument();
    });

    it('rejects oversized file (> 50 MB) with client-side validation error', () => {
      const onUploadSuccess = vi.fn();
      render(<ArtifactUploadForm onUploadSuccess={onUploadSuccess} />);

      const bigFile = new File(['x'], 'huge.iso', { type: 'application/octet-stream' });
      Object.defineProperty(bigFile, 'size', { value: 55 * 1024 * 1024 }); // 55 MB

      const fileInput = screen.getByLabelText('Select artifact file');
      fireEvent.change(fileInput, { target: { files: [bigFile] } });

      expect(
        screen.getByText(/File exceeds the maximum allowed size of 50 MB/i)
      ).toBeInTheDocument();
    });

    it('uploads valid file and triggers onUploadSuccess callback', async () => {
      const onUploadSuccess = vi.fn();
      vi.mocked(artifactService.uploadArtifact).mockResolvedValue(mockArtifact);

      render(
        <ArtifactUploadForm
          projectId="PRJ-202609-00001"
          onUploadSuccess={onUploadSuccess}
        />
      );

      const validFile = new File(['mock file content'], 'architecture_v1.pdf', {
        type: 'application/pdf',
      });
      const fileInput = screen.getByLabelText('Select artifact file');

      fireEvent.change(fileInput, { target: { files: [validFile] } });

      expect(screen.getByText('architecture_v1.pdf')).toBeInTheDocument();

      const submitBtn = screen.getByRole('button', { name: /Upload & Ingest Artifact/i });
      expect(submitBtn).not.toBeDisabled();

      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(artifactService.uploadArtifact).toHaveBeenCalledWith(
          expect.objectContaining({
            file: validFile,
            artifactCategory: 'SOURCE_CODE',
            projectId: 'PRJ-202609-00001',
          })
        );
        expect(onUploadSuccess).toHaveBeenCalledWith(mockArtifact);
        expect(
          screen.getByText(/Artifact "architecture_v1.pdf" uploaded successfully/i)
        ).toBeInTheDocument();
      });
    });

    it('handles and displays upload API errors gracefully', async () => {
      const onUploadSuccess = vi.fn();
      vi.mocked(artifactService.uploadArtifact).mockRejectedValue({
        response: {
          status: 403,
          data: {
            success: false,
            error: {
              code: 'FORBIDDEN',
              message: 'You do not have permission to upload artifacts to this project.',
            },
          },
        },
      });

      render(
        <ArtifactUploadForm
          projectId="PRJ-202609-00001"
          onUploadSuccess={onUploadSuccess}
        />
      );

      const validFile = new File(['mock content'], 'test.py', { type: 'text/x-python' });
      const fileInput = screen.getByLabelText('Select artifact file');

      fireEvent.change(fileInput, { target: { files: [validFile] } });
      const submitBtn = screen.getByRole('button', { name: /Upload & Ingest Artifact/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText('You do not have permission to upload artifacts to this project.')
        ).toBeInTheDocument();
      });
    });
  });

  describe('ProjectArtifactsPage', () => {
    it('renders project header, upload form, and existing artifacts', async () => {
      renderArtifactsPage();

      await waitFor(() => {
        expect(
          screen.getByText('Decentralized IPFS Academic Registry')
        ).toBeInTheDocument();
        expect(screen.getByText('PRJ-202609-00001')).toBeInTheDocument();
        expect(screen.getByText('architecture_v1.pdf')).toBeInTheDocument();
        expect(screen.getByText('Ingested Artifacts (1)')).toBeInTheDocument();
      });
    });

    it('handles project not found / API loading errors', async () => {
      vi.mocked(projectService.getProject).mockRejectedValue({
        response: {
          status: 404,
          data: {
            success: false,
            error: {
              code: 'PROJECT_NOT_FOUND',
              message: 'Project does not exist.',
            },
          },
        },
      });

      renderArtifactsPage();

      await waitFor(() => {
        expect(screen.getByText('Project does not exist.')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Retry Loading/i })).toBeInTheDocument();
      });
    });

    it('adds newly uploaded artifact to the displayed list in real-time', async () => {
      const newArtifact: ArtifactResponse = {
        public_id: 'ART-202609-99X11',
        file_name: 'test_suite.py',
        file_type: 'text/x-python',
        file_size_bytes: 4096,
        sha256_hash: 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
        artifact_category: 'SOURCE_CODE',
        uploaded_at: '2026-09-02T17:00:00Z',
      };

      vi.mocked(artifactService.uploadArtifact).mockResolvedValue(newArtifact);

      renderArtifactsPage();

      await waitFor(() => {
        expect(screen.getByText('architecture_v1.pdf')).toBeInTheDocument();
      });

      const fileInput = screen.getByLabelText('Select artifact file');
      const testFile = new File(['code'], 'test_suite.py', { type: 'text/x-python' });
      fireEvent.change(fileInput, { target: { files: [testFile] } });

      const submitBtn = screen.getByRole('button', { name: /Upload & Ingest Artifact/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(screen.getByText('test_suite.py')).toBeInTheDocument();
        expect(screen.getByText('Ingested Artifacts (2)')).toBeInTheDocument();
      });
    });
  });
});
