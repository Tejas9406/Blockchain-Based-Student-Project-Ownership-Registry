import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { VerificationPortalPage } from '../pages/verification/VerificationPortalPage';
import { VerificationDetailPage } from '../pages/verification/VerificationDetailPage';
import { verificationService } from '../services/verification.service';
import { VerificationResponseData } from '../types';

// Mock clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockImplementation(() => Promise.resolve()),
  },
});

// Mock verification service
vi.mock('../services/verification.service', () => ({
  verificationService: {
    verifyByRegistrationId: vi.fn(),
    verifyByHash: vi.fn(),
    verifyByFile: vi.fn(),
  },
}));

const mockVerifiedData: VerificationResponseData = {
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
    dispute_status: 'NONE',
    match_confirmed: true,
  },
};

describe('Ownership Verification Module Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('VerificationPortalPage — Public Search Portal', () => {
    it('renders portal title, subtitle, tabs, and form', () => {
      render(
        <MemoryRouter>
          <VerificationPortalPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Trustless Ownership Verification')).toBeInTheDocument();
      expect(screen.getByText('PUBLIC PROVENANCE PORTAL')).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /registration id/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /sha-256 digest/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /direct file verify/i })).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/REG-2026-A8F92D/i)).toBeInTheDocument();
    });

    it('validates empty registration ID input and blocks submission', async () => {
      render(
        <MemoryRouter>
          <VerificationPortalPage />
        </MemoryRouter>
      );

      const submitBtn = screen.getByRole('button', { name: /verify ownership proof/i });
      fireEvent.click(submitBtn);

      expect(screen.getByText(/please enter a registration id/i)).toBeInTheDocument();
    });

    it('switches to SHA-256 tab and verifies valid 64-char hash', async () => {
      vi.mocked(verificationService.verifyByHash).mockResolvedValueOnce({
        ...mockVerifiedData,
        verification_method: 'SHA256_HASH',
        matched_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      });

      render(
        <MemoryRouter>
          <VerificationPortalPage />
        </MemoryRouter>
      );

      const shaTab = screen.getByRole('tab', { name: /sha-256 digest/i });
      fireEvent.click(shaTab);

      const hashInput = screen.getByPlaceholderText(/9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08/i);
      fireEvent.change(hashInput, {
        target: { value: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08' },
      });

      const submitBtn = screen.getByRole('button', { name: /verify ownership proof/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(verificationService.verifyByHash).toHaveBeenCalledWith({
          sha256_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
          registration_id: undefined,
        });
      });

      expect(await screen.findByText('Direct File / Hash Match Confirmed')).toBeInTheDocument();
      expect(screen.getByText('Valid Ownership Proof')).toBeInTheDocument();
    });

    it('switches to File Upload tab and verifies uploaded artifact', async () => {
      vi.mocked(verificationService.verifyByFile).mockResolvedValueOnce({
        ...mockVerifiedData,
        verification_method: 'FILE_STREAM',
        matched_file_name: 'architecture_v1.pdf',
      });

      render(
        <MemoryRouter>
          <VerificationPortalPage />
        </MemoryRouter>
      );

      const fileTab = screen.getByRole('tab', { name: /direct file verify/i });
      fireEvent.click(fileTab);

      const file = new File(['sample academic artifact content'], 'architecture_v1.pdf', {
        type: 'application/pdf',
      });

      const fileInput = document.getElementById('file-verify-input') as HTMLInputElement;
      fireEvent.change(fileInput, { target: { files: [file] } });

      expect(screen.getByText('architecture_v1.pdf')).toBeInTheDocument();

      const submitBtn = screen.getByRole('button', { name: /verify ownership proof/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(verificationService.verifyByFile).toHaveBeenCalledWith(file, undefined);
      });

      expect(await screen.findByText('Direct File / Hash Match Confirmed')).toBeInTheDocument();
      expect(screen.getAllByText('architecture_v1.pdf').length).toBeGreaterThanOrEqual(1);
    });

    it('renders API error banner when verification request fails', async () => {
      vi.mocked(verificationService.verifyByHash).mockRejectedValueOnce({
        response: {
          data: {
            error: {
              code: 'NOT_FOUND',
              message: 'No registered project or artifact matched the provided hash digest.',
            },
          },
        },
      });

      render(
        <MemoryRouter>
          <VerificationPortalPage />
        </MemoryRouter>
      );

      const shaTab = screen.getByRole('tab', { name: /sha-256 digest/i });
      fireEvent.click(shaTab);

      const hashInput = screen.getByPlaceholderText(/9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08/i);
      fireEvent.change(hashInput, {
        target: { value: '0000000000000000000000000000000000000000000000000000000000000000' },
      });

      const submitBtn = screen.getByRole('button', { name: /verify ownership proof/i });
      fireEvent.click(submitBtn);

      expect(await screen.findByText(/no registered project or artifact matched/i)).toBeInTheDocument();
    });
  });

  describe('VerificationDetailPage — Dossier by Registration ID', () => {
    it('fetches and renders full verified dossier for valid registration ID', async () => {
      vi.mocked(verificationService.verifyByRegistrationId).mockResolvedValueOnce(mockVerifiedData);

      render(
        <MemoryRouter initialEntries={['/verify/REG-2026-A8F92D']}>
          <Routes>
            <Route path="/verify/:registrationId" element={<VerificationDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByTestId('verification-loading')).toBeInTheDocument();

      await waitFor(() => {
        expect(verificationService.verifyByRegistrationId).toHaveBeenCalledWith('REG-2026-A8F92D');
      });

      // Assert verified state and project info
      expect(await screen.findByText('REG-2026-A8F92D')).toBeInTheDocument();
      expect(screen.getByText('Valid Ownership Proof')).toBeInTheDocument();
      expect(screen.getAllByText('Decentralized IPFS Academic Registry').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('PRJ-202608-99B12')).toBeInTheDocument();
      expect(screen.getByText('Computer Science & Engineering')).toBeInTheDocument();
      expect(screen.getByText('National Institute of Technology')).toBeInTheDocument();

      // Assert on-chain proof
      expect(screen.getByText('Authoritative On-Chain EVM Blockchain Proof')).toBeInTheDocument();
      expect(screen.getByText('0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb')).toBeInTheDocument();
      expect(screen.getByText('0x5FbDB2315678afecb367f032d93F642f64180aa3')).toBeInTheDocument();
      expect(screen.getByText('0x70997970C51812dc3A010C7d01b50e0d17dc79C8')).toBeInTheDocument();
      expect(screen.getByText(/#142981/)).toBeInTheDocument();
    });

    it('renders disputed state when blockchain proof has active dispute status', async () => {
      const disputedData: VerificationResponseData = {
        ...mockVerifiedData,
        blockchain_proof: {
          ...mockVerifiedData.blockchain_proof!,
          dispute_status: 'OPEN',
        },
      };

      vi.mocked(verificationService.verifyByRegistrationId).mockResolvedValueOnce(disputedData);

      render(
        <MemoryRouter initialEntries={['/verify/REG-2026-A8F92D']}>
          <Routes>
            <Route path="/verify/:registrationId" element={<VerificationDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      expect(await screen.findByText(/Under Dispute \(OPEN\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Active Ownership Dispute Logged/i)).toBeInTheDocument();
    });

    it('handles not found (404) gracefully with friendly message', async () => {
      vi.mocked(verificationService.verifyByRegistrationId).mockRejectedValueOnce({
        response: {
          status: 404,
          data: {
            error: {
              code: 'NOT_FOUND',
              message: 'The requested project registration ID does not exist in the registry.',
            },
          },
        },
      });

      render(
        <MemoryRouter initialEntries={['/verify/REG-2026-NONEXIST']}>
          <Routes>
            <Route path="/verify/:registrationId" element={<VerificationDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      expect(await screen.findByText('Registration Proof Not Found')).toBeInTheDocument();
      expect(screen.getByText(/REG-2026-NONEXIST/i)).toBeInTheDocument();
      expect(screen.getByText('Search Another Registration')).toBeInTheDocument();
    });

    it('supports copying proof values to clipboard without altering content', async () => {
      vi.mocked(verificationService.verifyByRegistrationId).mockResolvedValueOnce(mockVerifiedData);

      render(
        <MemoryRouter initialEntries={['/verify/REG-2026-A8F92D']}>
          <Routes>
            <Route path="/verify/:registrationId" element={<VerificationDetailPage />} />
          </Routes>
        </MemoryRouter>
      );

      await screen.findByText('REG-2026-A8F92D');

      // Copy Registration ID
      const copyRegBtn = screen.getByLabelText(/copy registration id/i);
      fireEvent.click(copyRegBtn);
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('REG-2026-A8F92D');

      // Copy Composite SHA-256
      const copyShaBtn = screen.getByLabelText(/copy composite sha-256/i);
      fireEvent.click(copyShaBtn);
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
      );

      // Copy Transaction Hash
      const copyTxBtn = screen.getByLabelText(/copy transaction hash/i);
      fireEvent.click(copyTxBtn);
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        '0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb'
      );
    });
  });
});
