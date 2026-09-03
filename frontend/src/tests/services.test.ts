import { describe, it, expect, vi, afterEach } from 'vitest';
import { apiClient } from '../services/api';
import { authService } from '../services/auth.service';
import { projectService } from '../services/project.service';
import { artifactService } from '../services/artifact.service';
import { verificationService } from '../services/verification.service';
import { disputeService } from '../services/dispute.service';
import { certificateService } from '../services/certificate.service';

describe('API Service Layers', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('authService', () => {
    it('calls POST /auth/register with user registration payload', async () => {
      const mockPost = vi.spyOn(apiClient, 'post').mockResolvedValue({
        data: {
          success: true,
          data: { public_id: 'USR-123', email: 'test@student.edu', full_name: 'Test Student', role: 'STUDENT' },
          meta: { timestamp: '2026-08-31T18:50:00.000Z' },
        },
      } as any);

      const payload = {
        email: 'test@student.edu',
        password: 'Password123!',
        full_name: 'Test Student',
        institution_id: 'CS-001',
        department: 'Computer Science',
      };

      const result = await authService.register(payload);

      expect(mockPost).toHaveBeenCalledWith('/auth/register', payload);
      expect(result.public_id).toBe('USR-123');
    });

    it('calls POST /auth/login with user credentials', async () => {
      const mockPost = vi.spyOn(apiClient, 'post').mockResolvedValue({
        data: {
          success: true,
          data: {
            access_token: 'acc-tok',
            refresh_token: 'ref-tok',
            token_type: 'bearer',
            expires_in: 3600,
            user: { public_id: 'USR-123', email: 'test@student.edu', full_name: 'Test Student', role: 'STUDENT' },
          },
          meta: { timestamp: '2026-08-31T18:50:00.000Z' },
        },
      } as any);

      const payload = { email: 'test@student.edu', password: 'Password123!' };
      const result = await authService.login(payload);

      expect(mockPost).toHaveBeenCalledWith('/auth/login', payload);
      expect(result.access_token).toBe('acc-tok');
    });

    it('calls POST /auth/refresh with refresh token payload', async () => {
      const mockPost = vi.spyOn(apiClient, 'post').mockResolvedValue({
        data: {
          success: true,
          data: {
            access_token: 'new-acc-tok',
            refresh_token: 'new-ref-tok',
            token_type: 'bearer',
            expires_in: 3600,
          },
          meta: { timestamp: '2026-08-31T18:50:00.000Z' },
        },
      } as any);

      const payload = { refresh_token: 'old-ref-tok' };
      const result = await authService.refreshToken(payload);

      expect(mockPost).toHaveBeenCalledWith('/auth/refresh', payload);
      expect(result.access_token).toBe('new-acc-tok');
    });

    it('calls GET /auth/me to retrieve current user', async () => {
      const mockGet = vi.spyOn(apiClient, 'get').mockResolvedValue({
        data: {
          success: true,
          data: { public_id: 'USR-123', email: 'test@student.edu', full_name: 'Test Student', role: 'STUDENT' },
          meta: { timestamp: '2026-08-31T18:50:00.000Z' },
        },
      } as any);

      const result = await authService.getMe();
      expect(mockGet).toHaveBeenCalledWith('/auth/me');
      expect(result.email).toBe('test@student.edu');
    });
  });

  describe('projectService', () => {
    it('calls POST /projects to create a project', async () => {
      const mockPost = vi.spyOn(apiClient, 'post').mockResolvedValue({
        data: {
          success: true,
          data: { public_id: 'PRJ-123', slug: 'test-project', title: 'Test Project' },
          meta: { timestamp: '2026-08-31T18:50:00.000Z' },
        },
      } as any);

      const payload = {
        title: 'Test Project',
        abstract: 'Project abstract',
        category: 'AI',
        department: 'CSE',
        academic_year: '2025-2026',
      };

      const result = await projectService.createProject(payload);
      expect(mockPost).toHaveBeenCalledWith('/projects', payload);
      expect(result.slug).toBe('test-project');
    });

    it('calls GET /projects with query parameters', async () => {
      const mockGet = vi.spyOn(apiClient, 'get').mockResolvedValue({
        data: {
          success: true,
          data: [{ public_id: 'PRJ-123', title: 'Test Project' }],
          meta: { page: 1, page_size: 20, total_items: 1, total_pages: 1, has_next: false, has_prev: false, timestamp: '' },
        },
      } as any);

      const params = { page: 1, page_size: 10, category: 'AI' };
      const result = await projectService.listProjects(params);

      expect(mockGet).toHaveBeenCalledWith('/projects', { params });
      expect(result.data.length).toBe(1);
    });

    it('calls POST /projects/{id}/versions with optional idempotency key', async () => {
      const mockPost = vi.spyOn(apiClient, 'post').mockResolvedValue({
        data: {
          success: true,
          data: { public_id: 'VER-123', registration_id: 'REG-2026-ABCDE', version_tag: 'v1.0' },
          meta: { timestamp: '2026-08-31T18:50:00.000Z' },
        },
      } as any);

      const payload = {
        version_tag: 'v1.0',
        lifecycle_stage: 'DESIGN' as const,
        title: 'Initial Architecture',
        artifact_ids: ['ART-001'],
      };

      const result = await projectService.createVersion('PRJ-123', payload, 'idem-key-123');

      expect(mockPost).toHaveBeenCalledWith(
        '/projects/PRJ-123/versions',
        payload,
        { headers: { 'Idempotency-Key': 'idem-key-123' } }
      );
      expect(result.registration_id).toBe('REG-2026-ABCDE');
    });
  });

  describe('artifactService', () => {
    it('calls POST /artifacts/upload with multipart form data and progress callback', async () => {
      const mockPost = vi.spyOn(apiClient, 'post').mockResolvedValue({
        data: {
          success: true,
          data: { public_id: 'ART-123', file_name: 'paper.pdf', file_size_bytes: 1024 },
          meta: { timestamp: '2026-08-31T18:50:00.000Z' },
        },
      } as any);

      const onProgress = vi.fn();
      const mockFile = new File(['dummy content'], 'paper.pdf', { type: 'application/pdf' });
      const result = await artifactService.uploadArtifact({
        file: mockFile,
        artifactCategory: 'DOCUMENTATION',
        projectId: 'PRJ-123',
        onUploadProgress: onProgress,
      });

      expect(mockPost).toHaveBeenCalledWith(
        '/artifacts/upload',
        expect.any(FormData),
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: onProgress,
        }
      );
      expect(result.public_id).toBe('ART-123');
    });
  });

  describe('verificationService', () => {
    it('calls GET /verification/verify-registration/{id}', async () => {
      const mockGet = vi.spyOn(apiClient, 'get').mockResolvedValue({
        data: {
          success: true,
          data: { is_valid: true, registration_id: 'REG-2026-A8F92D' },
          meta: { timestamp: '2026-08-31T18:50:00.000Z' },
        },
      } as any);

      const result = await verificationService.verifyByRegistrationId('REG-2026-A8F92D');
      expect(mockGet).toHaveBeenCalledWith('/verification/verify-registration/REG-2026-A8F92D');
      expect(result.is_valid).toBe(true);
    });

    it('calls POST /verification/verify-hash with SHA-256 hash', async () => {
      const mockPost = vi.spyOn(apiClient, 'post').mockResolvedValue({
        data: {
          success: true,
          data: { is_valid: true, registration_id: 'REG-2026-A8F92D' },
          meta: { timestamp: '2026-08-31T18:50:00.000Z' },
        },
      } as any);

      const payload = { sha256_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08' };
      const result = await verificationService.verifyByHash(payload);

      expect(mockPost).toHaveBeenCalledWith('/verification/verify-hash', payload);
      expect(result.is_valid).toBe(true);
    });
  });

  describe('disputeService', () => {
    it('calls POST /disputes to file a dispute claim', async () => {
      const mockPost = vi.spyOn(apiClient, 'post').mockResolvedValue({
        data: {
          success: true,
          data: { public_id: 'DSP-123', project_id: 'PRJ-123', status: 'OPEN' },
          meta: { timestamp: '2026-08-31T18:50:00.000Z' },
        },
      } as any);

      const payload = {
        project_id: 'PRJ-123',
        dispute_type: 'PLAGIARISM' as const,
        claim_description: 'Plagiarized code from prior work',
      };

      const result = await disputeService.raiseDispute(payload);
      expect(mockPost).toHaveBeenCalledWith('/disputes', payload);
      expect(result.status).toBe('OPEN');
    });

    it('calls PATCH /admin/disputes/{id}/adjudicate to resolve a dispute', async () => {
      const mockPatch = vi.spyOn(apiClient, 'patch').mockResolvedValue({
        data: {
          success: true,
          data: { public_id: 'DSP-123', status: 'RESOLVED' },
          meta: { timestamp: '2026-08-31T18:50:00.000Z' },
        },
      } as any);

      const payload = {
        resolution_status: 'RESOLVED' as const,
        resolution_notes: 'Claim verified on-chain',
      };

      const result = await disputeService.adjudicateDispute('DSP-123', payload);
      expect(mockPatch).toHaveBeenCalledWith('/admin/disputes/DSP-123/adjudicate', payload);
      expect(result.status).toBe('RESOLVED');
    });
  });

  describe('certificateService', () => {
    it('calls GET /certificates/{registrationId} to get metadata', async () => {
      const mockGet = vi.spyOn(apiClient, 'get').mockResolvedValue({
        data: {
          success: true,
          data: { registration_id: 'REG-2026-A8F92D', project_title: 'Title' },
          meta: { timestamp: '2026-08-31T18:50:00.000Z' },
        },
      } as any);

      const result = await certificateService.getCertificateMetadata('REG-2026-A8F92D');
      expect(mockGet).toHaveBeenCalledWith('/certificates/REG-2026-A8F92D');
      expect(result.registration_id).toBe('REG-2026-A8F92D');
    });

    it('generates correct download and QR URLs', () => {
      const downloadUrl = certificateService.getCertificateDownloadUrl('REG-2026-A8F92D');
      const qrUrl = certificateService.getCertificateQrUrl('REG-2026-A8F92D');

      expect(downloadUrl).toContain('/certificates/REG-2026-A8F92D/download');
      expect(qrUrl).toContain('/certificates/REG-2026-A8F92D/qr');
    });
  });
});
