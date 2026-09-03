import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DisputesPage } from '../pages/disputes/DisputesPage';
import { DisputeDetailPage } from '../pages/disputes/DisputeDetailPage';
import { disputeService } from '../services/dispute.service';
import { projectService } from '../services/project.service';
import { DisputeDetailResponse } from '../types';

// Mock clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockImplementation(() => Promise.resolve()),
  },
});

// Mock dispute & project services
vi.mock('../services/dispute.service', () => ({
  disputeService: {
    raiseDispute: vi.fn(),
    getDispute: vi.fn(),
    listProjectDisputes: vi.fn(),
  },
}));

vi.mock('../services/project.service', () => ({
  projectService: {
    listProjects: vi.fn(),
    getProject: vi.fn(),
  },
}));

const mockOpenDispute: DisputeDetailResponse = {
  public_id: 'DSP-202609-A8F92',
  project_public_id: 'PRJ-202609-99B12',
  project_title: 'Decentralized Academic Provenance Protocol',
  registration_id: 'REG-2026-A8F92D',
  dispute_type: 'PLAGIARISM',
  claim_description: 'The core consensus architecture and diagram were copied from our 2024 IEEE paper without attribution.',
  evidence_url: 'bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m',
  status: 'OPEN',
  transaction_hash: '0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb',
  claimant: {
    public_id: 'USR-202609-C1234',
    full_name: 'Dr. Siddharth Rao',
    institution_id: 'Indian Institute of Technology',
  },
  created_at: '2026-08-31T18:50:00.000Z',
};

const mockResolvedDispute: DisputeDetailResponse = {
  public_id: 'DSP-202609-B4567',
  project_public_id: 'PRJ-202609-88C34',
  project_title: 'Zero-Knowledge Credential Issuer',
  registration_id: 'REG-2026-B4567E',
  dispute_type: 'UNAUTHORIZED_USE',
  claim_description: 'Proprietary dataset was utilized without explicit consent from research group.',
  evidence_url: 'https://gateway.pinata.cloud/ipfs/bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi',
  status: 'RESOLVED',
  resolution_notes: 'Adjudication panel confirmed evidence: dataset was released under non-commercial attribution license.',
  transaction_hash: '0x71c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb',
  resolution_transaction_hash: '0x81c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb',
  claimant: {
    public_id: 'USR-202609-C5678',
    full_name: 'Priya Sharma',
    institution_id: 'National Institute of Technology',
  },
  created_at: '2026-08-20T10:00:00.000Z',
  resolved_at: '2026-08-25T14:30:00.000Z',
};

describe('Frontend Disputes & Resolution Module Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('DisputesPage — Catalog & Ingestion', () => {
    it('renders header, file dispute button, and dispute cards', async () => {
      vi.mocked(projectService.listProjects).mockResolvedValueOnce({
        success: true,
        data: [{ public_id: 'PRJ-202609-99B12' }] as any,
        meta: {} as any,
      });
      vi.mocked(disputeService.listProjectDisputes).mockResolvedValueOnce([mockOpenDispute]);

      render(
        <MemoryRouter initialEntries={['/disputes']}>
          <DisputesPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Ownership Claims & Dispute Registry')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /file dispute claim/i })).toBeInTheDocument();

      expect(await screen.findByText('DSP-202609-A8F92')).toBeInTheDocument();
      expect(screen.getByText('Decentralized Academic Provenance Protocol')).toBeInTheDocument();
      expect(screen.getByText('Plagiarism')).toBeInTheDocument();
      expect(screen.getByText('Open Claim')).toBeInTheDocument();
    });

    it('renders empty state when no disputes exist', async () => {
      vi.mocked(projectService.listProjects).mockResolvedValueOnce({
        success: true,
        data: [],
        meta: {} as any,
      });

      render(
        <MemoryRouter initialEntries={['/disputes']}>
          <DisputesPage />
        </MemoryRouter>
      );

      expect(await screen.findByTestId('disputes-empty')).toBeInTheDocument();
      expect(screen.getByText('No Dispute Claims Logged')).toBeInTheDocument();
    });

    it('opens CreateDisputeModal, validates inputs, and submits new dispute', async () => {
      vi.mocked(projectService.listProjects).mockResolvedValueOnce({
        success: true,
        data: [],
        meta: {} as any,
      });
      vi.mocked(disputeService.raiseDispute).mockResolvedValueOnce(mockOpenDispute);

      render(
        <MemoryRouter initialEntries={['/disputes']}>
          <DisputesPage />
        </MemoryRouter>
      );

      // Open Modal
      const fileBtn = await screen.findByRole('button', { name: /file dispute claim/i });
      fireEvent.click(fileBtn);

      expect(screen.getByRole('heading', { name: /file ownership dispute claim/i })).toBeInTheDocument();

      // Submit with empty inputs -> validation error
      const submitBtn = screen.getByRole('button', { name: /submit claim/i });
      fireEvent.click(submitBtn);

      expect(
        screen.getByText(/please specify either a target project id or certificate registration id/i)
      ).toBeInTheDocument();

      // Fill in valid inputs
      const projInput = screen.getByLabelText(/target project id/i);
      fireEvent.change(projInput, { target: { value: 'PRJ-202609-99B12' } });

      const descInput = screen.getByLabelText(/factual claim & prior art details/i);
      fireEvent.change(descInput, {
        target: {
          value: 'The core consensus architecture was copied from our prior published paper.',
        },
      });

      const evidenceInput = screen.getByLabelText(/prior art evidence/i);
      fireEvent.change(evidenceInput, {
        target: { value: 'bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m' },
      });

      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(disputeService.raiseDispute).toHaveBeenCalledWith({
          project_id: 'PRJ-202609-99B12',
          registration_id: undefined,
          dispute_type: 'PLAGIARISM',
          claim_description: 'The core consensus architecture was copied from our prior published paper.',
          evidence_url: 'bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m',
        });
      });

      // Modal closed and dispute card added to list
      expect(await screen.findByText('DSP-202609-A8F92')).toBeInTheDocument();
    });

    it('renders conflict error banner when target project has active dispute (409)', async () => {
      vi.mocked(projectService.listProjects).mockResolvedValueOnce({
        success: true,
        data: [],
        meta: {} as any,
      });
      vi.mocked(disputeService.raiseDispute).mockRejectedValueOnce({
        response: {
          status: 409,
          data: {
            error: {
              code: 'ACTIVE_DISPUTE_EXISTS',
              message: 'An active dispute is already open for this project record.',
            },
          },
        },
      });

      render(
        <MemoryRouter initialEntries={['/disputes']}>
          <DisputesPage />
        </MemoryRouter>
      );

      const fileBtn = await screen.findByRole('button', { name: /file dispute claim/i });
      fireEvent.click(fileBtn);

      const projInput = screen.getByLabelText(/target project id/i);
      fireEvent.change(projInput, { target: { value: 'PRJ-202609-99B12' } });

      const descInput = screen.getByLabelText(/factual claim & prior art details/i);
      fireEvent.change(descInput, {
        target: { value: 'Valid dispute claim description with more than 10 characters.' },
      });

      const submitBtn = screen.getByRole('button', { name: /submit claim/i });
      fireEvent.click(submitBtn);

      expect(
        await screen.findByText(/an active dispute is already open for this project record/i)
      ).toBeInTheDocument();
    });
  });

  describe('DisputeDetailPage — Full Dossier View', () => {
    it('fetches and renders full dispute detail dossier', async () => {
      vi.mocked(disputeService.getDispute).mockResolvedValueOnce(mockOpenDispute);

      render(
        <MemoryRouter initialEntries={['/disputes/DSP-202609-A8F92']}>
          <Routes>
            <Route path="/disputes/:disputeId" element={<DisputeDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByTestId('dispute-detail-loading')).toBeInTheDocument();

      await waitFor(() => {
        expect(disputeService.getDispute).toHaveBeenCalledWith('DSP-202609-A8F92');
      });

      expect(await screen.findByText('DSP-202609-A8F92')).toBeInTheDocument();
      expect(screen.getByText('Decentralized Academic Provenance Protocol')).toBeInTheDocument();
      expect(screen.getByText('Dr. Siddharth Rao')).toBeInTheDocument();
      expect(screen.getByText('Indian Institute of Technology')).toBeInTheDocument();
      expect(screen.getByText(/The core consensus architecture and diagram were copied/i)).toBeInTheDocument();
      expect(screen.getByText('bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m')).toBeInTheDocument();
      expect(screen.getByText('0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb')).toBeInTheDocument();
    });

    it('renders adjudication outcome and resolution notes for resolved disputes', async () => {
      vi.mocked(disputeService.getDispute).mockResolvedValueOnce(mockResolvedDispute);

      render(
        <MemoryRouter initialEntries={['/disputes/DSP-202609-B4567']}>
          <Routes>
            <Route path="/disputes/:disputeId" element={<DisputeDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      expect(await screen.findByTestId('adjudication-outcome')).toBeInTheDocument();
      expect(screen.getAllByText('Resolved (Claim Upheld)').length).toBeGreaterThanOrEqual(1);
      expect(
        screen.getByText(/Adjudication panel confirmed evidence: dataset was released/i)
      ).toBeInTheDocument();
      expect(screen.getByText('0x81c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb')).toBeInTheDocument();
    });

    it('handles not-found (404) gracefully with return link', async () => {
      vi.mocked(disputeService.getDispute).mockRejectedValueOnce({
        response: {
          status: 404,
          data: {
            error: {
              code: 'NOT_FOUND',
              message: 'Dispute record not found.',
            },
          },
        },
      });

      render(
        <MemoryRouter initialEntries={['/disputes/DSP-NONEXIST']}>
          <Routes>
            <Route path="/disputes/:disputeId" element={<DisputeDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      expect(await screen.findByText('Dispute Record Not Found')).toBeInTheDocument();
      expect(screen.getByText(/DSP-NONEXIST/i)).toBeInTheDocument();
      expect(screen.getByText('Return to Disputes List')).toBeInTheDocument();
    });

    it('copies evidence URL and transaction hashes to clipboard', async () => {
      vi.mocked(disputeService.getDispute).mockResolvedValueOnce(mockResolvedDispute);

      render(
        <MemoryRouter initialEntries={['/disputes/DSP-202609-B4567']}>
          <Routes>
            <Route path="/disputes/:disputeId" element={<DisputeDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      await screen.findByText('DSP-202609-B4567');

      // Copy Evidence URL
      const copyEvidenceBtn = screen.getByLabelText(/copy evidence url/i);
      fireEvent.click(copyEvidenceBtn);
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        'https://gateway.pinata.cloud/ipfs/bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi'
      );

      // Copy Transaction Hash
      const copyTxBtn = screen.getByLabelText(/copy transaction hash/i);
      fireEvent.click(copyTxBtn);
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        '0x71c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb'
      );

      // Copy Resolution Transaction Hash
      const copyResTxBtn = screen.getByLabelText(/copy resolution transaction hash/i);
      fireEvent.click(copyResTxBtn);
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        '0x81c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb'
      );
    });
  });
});
