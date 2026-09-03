import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DisputesPage } from '../pages/disputes/DisputesPage';
import { DisputeDetailPage } from '../pages/disputes/DisputeDetailPage';
import { AdminAdjudicationModal } from '../components/disputes/AdminAdjudicationModal';
import { AdminAdjudicationPanel } from '../components/disputes/AdminAdjudicationPanel';
import { disputeService } from '../services/dispute.service';
import { projectService } from '../services/project.service';
import { AuthContext, AuthContextType } from '../context/AuthContext';
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
    adjudicateDispute: vi.fn(),
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

const createMockAuthContext = (overrides?: Partial<AuthContextType>): AuthContextType => ({
  user: {
    public_id: 'USR-202609-ADMIN1',
    email: 'admin@sih2026.edu',
    full_name: 'System Admin',
    role: 'ADMIN',
    institution_id: 'INST-ADMIN-01',
    department: 'Registry Administration',
  },
  isAuthenticated: true,
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  refreshUser: vi.fn(),
  ...overrides,
});

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

    it('opens CreateDisputeModal, validates inputs, and submits new dispute', async () => {
      vi.mocked(projectService.listProjects).mockResolvedValue({
        success: true,
        data: [
          {
            public_id: 'PRJ-202609-99B12',
            title: 'Decentralized Academic Provenance Protocol',
            current_lifecycle_stage: 'FINAL',
          },
        ] as any,
        meta: {} as any,
      });
      vi.mocked(disputeService.listProjectDisputes).mockResolvedValue([mockOpenDispute]);
      vi.mocked(disputeService.raiseDispute).mockResolvedValueOnce(mockOpenDispute);

      render(
        <MemoryRouter initialEntries={['/disputes']}>
          <DisputesPage />
        </MemoryRouter>
      );

      const fileBtn = screen.getByRole('button', { name: /file dispute claim/i });
      fireEvent.click(fileBtn);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('File Ownership Dispute Claim')).toBeInTheDocument();

      // Submit with empty fields
      const submitBtn = screen.getByRole('button', { name: /submit claim/i });
      fireEvent.click(submitBtn);

      expect(
        await screen.findByText(/Please specify either a Target Project ID or Certificate Registration ID/i)
      ).toBeInTheDocument();

      // Fill in valid details
      const regIdInput = screen.getByPlaceholderText(/e\.g\. REG-2026-A8F92/i);
      fireEvent.change(regIdInput, { target: { value: 'REG-2026-A8F92D' } });

      const descInput = screen.getByPlaceholderText(/Explain why this project infringes/i);
      fireEvent.change(descInput, {
        target: {
          value: 'Detailed claim explanation regarding copied architecture diagram and core protocol design.',
        },
      });

      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(disputeService.raiseDispute).toHaveBeenCalledWith(
          expect.objectContaining({
            registration_id: 'REG-2026-A8F92D',
            dispute_type: 'PLAGIARISM',
          })
        );
      });
    });
  });

  describe('DisputeDetailPage — Dossier & Timeline', () => {
    it('fetches and renders complete dispute dossier metadata', async () => {
      vi.mocked(disputeService.getDispute).mockResolvedValueOnce(mockOpenDispute);

      render(
        <MemoryRouter initialEntries={['/disputes/DSP-202609-A8F92']}>
          <Routes>
            <Route path="/disputes/:disputeId" element={<DisputeDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      expect((await screen.findAllByText('DSP-202609-A8F92')).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Decentralized Academic Provenance Protocol')).toBeInTheDocument();
      expect(screen.getByText('Dr. Siddharth Rao')).toBeInTheDocument();
      expect(screen.getByText('Indian Institute of Technology')).toBeInTheDocument();
      expect(screen.getByText('bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m')).toBeInTheDocument();
      expect(screen.getByText('0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb')).toBeInTheDocument();
    });

    it('renders adjudication outcome dossier for resolved dispute', async () => {
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

  describe('Admin Dispute Adjudication Workflow', () => {
    it('renders admin adjudication panel for authenticated ADMIN user on active dispute', () => {
      const auth = createMockAuthContext({
        user: {
          public_id: 'USR-202609-ADMIN1',
          email: 'admin@sih2026.edu',
          full_name: 'Registry Administrator',
          role: 'ADMIN',
          institution_id: 'INST-01',
          department: 'Admin',
        },
      });

      render(
        <AuthContext.Provider value={auth}>
          <AdminAdjudicationPanel dispute={mockOpenDispute} onDisputeUpdated={vi.fn()} />
        </AuthContext.Provider>
      );

      expect(screen.getByTestId('admin-adjudication-panel')).toBeInTheDocument();
      expect(screen.getByText('Institutional Adjudication Authority')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /adjudicate claim/i })).toBeInTheDocument();
    });

    it('hides admin adjudication panel for non-admin users (STUDENT, FACULTY, VERIFIER)', () => {
      const studentAuth = createMockAuthContext({
        user: {
          public_id: 'USR-202609-STU1',
          email: 'student@sih2026.edu',
          full_name: 'Student User',
          role: 'STUDENT',
          institution_id: 'INST-01',
          department: 'CSE',
        },
      });

      const { container } = render(
        <AuthContext.Provider value={studentAuth}>
          <AdminAdjudicationPanel dispute={mockOpenDispute} onDisputeUpdated={vi.fn()} />
        </AuthContext.Provider>
      );

      expect(container.firstChild).toBeNull();
    });

    it('displays lock notice and disables adjudication for terminal dispute (RESOLVED/REJECTED)', () => {
      const auth = createMockAuthContext();

      render(
        <AuthContext.Provider value={auth}>
          <AdminAdjudicationPanel dispute={mockResolvedDispute} onDisputeUpdated={vi.fn()} />
        </AuthContext.Provider>
      );

      expect(screen.getByText('Adjudication Concluded')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /adjudicate claim/i })).not.toBeInTheDocument();
    });

    it('opens AdminAdjudicationModal and enforces validation on notes and confirmation', async () => {
      render(
        <AdminAdjudicationModal
          dispute={mockOpenDispute}
          isOpen={true}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Adjudicate Dispute Claim')).toBeInTheDocument();

      // Submit without entering notes
      const submitBtn = screen.getByRole('button', { name: /submit final adjudication/i });
      fireEvent.click(submitBtn);

      expect(
        await screen.findByText('Resolution rationale notes must be at least 5 characters long.')
      ).toBeInTheDocument();
      expect(disputeService.adjudicateDispute).not.toHaveBeenCalled();

      // Enter notes but do not check confirmation
      const textarea = screen.getByPlaceholderText(/Detail the factual findings/i);
      fireEvent.change(textarea, {
        target: { value: 'Claimant provided incomplete evidence of prior art publication.' },
      });

      fireEvent.click(submitBtn);
      expect(
        await screen.findByText(
          /Please confirm that you have reviewed the evidence and authorize this on-chain adjudication/i
        )
      ).toBeInTheDocument();
    });

    it('submits REJECTED (Claim Dismissed) outcome and calls disputeService.adjudicateDispute', async () => {
      const updatedDispute: DisputeDetailResponse = {
        ...mockOpenDispute,
        status: 'REJECTED',
        resolution_notes: 'Claim dismissed: respondent verified repository precedence on-chain.',
        resolution_transaction_hash: '0x9999999999999999999999999999999999999999999999999999999999999999',
      };
      vi.mocked(disputeService.adjudicateDispute).mockResolvedValueOnce(updatedDispute);

      const handleSuccess = vi.fn();
      const handleClose = vi.fn();

      render(
        <AdminAdjudicationModal
          dispute={mockOpenDispute}
          isOpen={true}
          onClose={handleClose}
          onSuccess={handleSuccess}
        />
      );

      const notesInput = screen.getByPlaceholderText(/Detail the factual findings/i);
      fireEvent.change(notesInput, {
        target: { value: 'Claim dismissed: respondent verified repository precedence on-chain.' },
      });

      const confirmCheckbox = screen.getByRole('checkbox');
      fireEvent.click(confirmCheckbox);

      const submitBtn = screen.getByRole('button', { name: /submit final adjudication/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(disputeService.adjudicateDispute).toHaveBeenCalledWith('DSP-202609-A8F92', {
          resolution_status: 'REJECTED',
          resolution_notes: 'Claim dismissed: respondent verified repository precedence on-chain.',
        });
        expect(handleSuccess).toHaveBeenCalledWith(updatedDispute);
        expect(handleClose).toHaveBeenCalled();
      });
    });

    it('submits RESOLVED (Claim Upheld) outcome when selected', async () => {
      const updatedDispute: DisputeDetailResponse = {
        ...mockOpenDispute,
        status: 'RESOLVED',
        resolution_notes: 'Claim upheld: infringement confirmed by academic committee.',
        resolution_transaction_hash: '0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
      };
      vi.mocked(disputeService.adjudicateDispute).mockResolvedValueOnce(updatedDispute);

      const handleSuccess = vi.fn();

      render(
        <AdminAdjudicationModal
          dispute={mockOpenDispute}
          isOpen={true}
          onClose={vi.fn()}
          onSuccess={handleSuccess}
        />
      );

      // Select RESOLVED (Claim Upheld)
      const resolvedBtn = screen.getByRole('button', { name: /RESOLVED \(Claim Upheld\)/i });
      fireEvent.click(resolvedBtn);

      const notesInput = screen.getByPlaceholderText(/Detail the factual findings/i);
      fireEvent.change(notesInput, {
        target: { value: 'Claim upheld: infringement confirmed by academic committee.' },
      });

      const confirmCheckbox = screen.getByRole('checkbox');
      fireEvent.click(confirmCheckbox);

      const submitBtn = screen.getByRole('button', { name: /submit final adjudication/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(disputeService.adjudicateDispute).toHaveBeenCalledWith('DSP-202609-A8F92', {
          resolution_status: 'RESOLVED',
          resolution_notes: 'Claim upheld: infringement confirmed by academic committee.',
        });
        expect(handleSuccess).toHaveBeenCalledWith(updatedDispute);
      });
    });

    it('handles 403 Forbidden error when non-admin attempts adjudication', async () => {
      vi.mocked(disputeService.adjudicateDispute).mockRejectedValueOnce({
        response: {
          status: 403,
          data: {
            error: {
              code: 'FORBIDDEN',
              message: 'Insufficient permissions (ADMIN role required).',
            },
          },
        },
      });

      render(
        <AdminAdjudicationModal
          dispute={mockOpenDispute}
          isOpen={true}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      const notesInput = screen.getByPlaceholderText(/Detail the factual findings/i);
      fireEvent.change(notesInput, {
        target: { value: 'Administrative decision notes test.' },
      });
      fireEvent.click(screen.getByRole('checkbox'));

      const submitBtn = screen.getByRole('button', { name: /submit final adjudication/i });
      fireEvent.click(submitBtn);

      expect(
        await screen.findByText('Insufficient permissions (ADMIN role required).')
      ).toBeInTheDocument();
    });

    it('handles 409 Conflict error when dispute is already resolved', async () => {
      vi.mocked(disputeService.adjudicateDispute).mockRejectedValueOnce({
        response: {
          status: 409,
          data: {
            error: {
              code: 'DISPUTE_ALREADY_RESOLVED',
              message: "Dispute 'DSP-202609-A8F92' is already RESOLVED and cannot be re-adjudicated.",
            },
          },
        },
      });

      render(
        <AdminAdjudicationModal
          dispute={mockOpenDispute}
          isOpen={true}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      const notesInput = screen.getByPlaceholderText(/Detail the factual findings/i);
      fireEvent.change(notesInput, {
        target: { value: 'Administrative decision notes test.' },
      });
      fireEvent.click(screen.getByRole('checkbox'));

      const submitBtn = screen.getByRole('button', { name: /submit final adjudication/i });
      fireEvent.click(submitBtn);

      expect(
        await screen.findByText("Dispute 'DSP-202609-A8F92' is already RESOLVED and cannot be re-adjudicated.")
      ).toBeInTheDocument();
    });

    it('handles 502/504 Blockchain Gateway Failure error gracefully', async () => {
      vi.mocked(disputeService.adjudicateDispute).mockRejectedValueOnce({
        response: {
          status: 502,
          data: {
            error: {
              code: 'BLOCKCHAIN_TRANSACTION_FAILED',
              message: 'Failed to broadcast resolveDispute transaction to the smart contract relayer.',
            },
          },
        },
      });

      render(
        <AdminAdjudicationModal
          dispute={mockOpenDispute}
          isOpen={true}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      const notesInput = screen.getByPlaceholderText(/Detail the factual findings/i);
      fireEvent.change(notesInput, {
        target: { value: 'Administrative decision notes test.' },
      });
      fireEvent.click(screen.getByRole('checkbox'));

      const submitBtn = screen.getByRole('button', { name: /submit final adjudication/i });
      fireEvent.click(submitBtn);

      expect(
        await screen.findByText('Failed to broadcast resolveDispute transaction to the smart contract relayer.')
      ).toBeInTheDocument();
    });

    it('updates DisputeDetailPage live when admin finishes adjudication', async () => {
      vi.mocked(disputeService.getDispute).mockResolvedValueOnce(mockOpenDispute);
      const adjudicatedOutcome: DisputeDetailResponse = {
        ...mockOpenDispute,
        status: 'RESOLVED',
        resolution_notes: 'Claim upheld on-chain after formal review.',
        resolution_transaction_hash: '0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
      };
      vi.mocked(disputeService.adjudicateDispute).mockResolvedValueOnce(adjudicatedOutcome);

      const auth = createMockAuthContext();

      render(
        <AuthContext.Provider value={auth}>
          <MemoryRouter initialEntries={['/disputes/DSP-202609-A8F92']}>
            <Routes>
              <Route path="/disputes/:disputeId" element={<DisputeDetailPage />} />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      );

      // Verify loaded initial open state
      expect((await screen.findAllByText('DSP-202609-A8F92')).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByRole('button', { name: /adjudicate claim/i })).toBeInTheDocument();

      // Open Modal
      fireEvent.click(screen.getByRole('button', { name: /adjudicate claim/i }));
      expect(screen.getByRole('dialog')).toBeInTheDocument();

      // Select RESOLVED
      fireEvent.click(screen.getByRole('button', { name: /RESOLVED \(Claim Upheld\)/i }));

      // Fill in notes and checkbox
      fireEvent.change(screen.getByPlaceholderText(/Detail the factual findings/i), {
        target: { value: 'Claim upheld on-chain after formal review.' },
      });
      fireEvent.click(screen.getByRole('checkbox'));

      // Submit
      fireEvent.click(screen.getByRole('button', { name: /submit final adjudication/i }));

      await waitFor(() => {
        expect(disputeService.adjudicateDispute).toHaveBeenCalledWith('DSP-202609-A8F92', {
          resolution_status: 'RESOLVED',
          resolution_notes: 'Claim upheld on-chain after formal review.',
        });
      });

      // Detail page updates with adjudicated outcome
      expect(await screen.findByText('Claim upheld on-chain after formal review.')).toBeInTheDocument();
      expect(screen.getByText('0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb')).toBeInTheDocument();
      expect(screen.getByText('Adjudication Concluded')).toBeInTheDocument();
    });
  });
});
