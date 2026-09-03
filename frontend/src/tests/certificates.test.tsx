import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { CertificateDetailPage } from '../pages/certificates/CertificateDetailPage';
import { certificateService } from '../services/certificate.service';
import { CertificateMetadataData } from '../types';

// Mock clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockImplementation(() => Promise.resolve()),
  },
});

// Mock URL.createObjectURL and revokeObjectURL
window.URL.createObjectURL = vi.fn().mockReturnValue('blob:http://localhost/test-blob');
window.URL.revokeObjectURL = vi.fn();

// Mock certificate service
vi.mock('../services/certificate.service', () => ({
  certificateService: {
    getCertificateMetadata: vi.fn(),
    downloadCertificatePdf: vi.fn(),
    getCertificateDownloadUrl: vi.fn(),
    getCertificateQrUrl: vi.fn(),
  },
}));

const mockCertificateData: CertificateMetadataData = {
  registration_id: 'REG-2026-A8F92D',
  project_title: 'Decentralized Academic Provenance Protocol',
  version_tag: 'v1.0',
  lifecycle_stage: 'FINAL',
  authors: ['Tejas Sharma', 'Aman Verma'],
  institution: 'National Institute of Technology',
  department: 'Computer Science & Engineering',
  anchored_timestamp: '2026-08-31T18:50:00.000Z',
  transaction_hash: '0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb',
  block_number: 1024,
  composite_sha256: 'a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8',
  ipfs_root_cid: 'bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi',
  verification_url: 'https://registry.sih2026.edu/verify/REG-2026-A8F92D',
  qr_code_svg_url: 'https://registry.sih2026.edu/api/v1/certificates/REG-2026-A8F92D/qr.svg',
  pdf_download_url: 'https://registry.sih2026.edu/api/v1/certificates/REG-2026-A8F92D/download',
  dispute_status: 'NONE',
};

describe('Ownership Certificates & QR Module Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders certificate loading state initially', async () => {
    vi.mocked(certificateService.getCertificateMetadata).mockReturnValue(new Promise(() => {}));

    render(
      <MemoryRouter initialEntries={['/certificates/REG-2026-A8F92D']}>
        <Routes>
          <Route path="/certificates/:registrationId" element={<CertificateDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('certificate-loading')).toBeInTheDocument();
    expect(screen.getByText(/Retrieving Ownership Certificate/i)).toBeInTheDocument();
  });

  it('fetches and renders full certificate preview with all metadata fields', async () => {
    vi.mocked(certificateService.getCertificateMetadata).mockResolvedValueOnce(mockCertificateData);

    render(
      <MemoryRouter initialEntries={['/certificates/REG-2026-A8F92D']}>
        <Routes>
          <Route path="/certificates/:registrationId" element={<CertificateDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(certificateService.getCertificateMetadata).toHaveBeenCalledWith('REG-2026-A8F92D');
    });

    // Verification seal & title
    expect(await screen.findByText(/Certificate of Project Ownership & Provenance/i)).toBeInTheDocument();
    expect(screen.getByText(/REGISTRATION ID: REG-2026-A8F92D/i)).toBeInTheDocument();

    // Project title & details
    expect(screen.getByText('Decentralized Academic Provenance Protocol')).toBeInTheDocument();
    expect(screen.getByText('Version v1.0')).toBeInTheDocument();
    expect(screen.getByText('Stage: FINAL')).toBeInTheDocument();
    expect(screen.getByText('Computer Science & Engineering')).toBeInTheDocument();

    // Authors & institution
    expect(screen.getByText('Tejas Sharma')).toBeInTheDocument();
    expect(screen.getByText('Aman Verma')).toBeInTheDocument();
    expect(screen.getByText(/National Institute of Technology/i)).toBeInTheDocument();

    // Cryptographic proof
    expect(screen.getByText('0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb')).toBeInTheDocument();
    expect(screen.getByText('a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8')).toBeInTheDocument();
    expect(screen.getByText('bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi')).toBeInTheDocument();
    expect(screen.getByText(/Block #1024/i)).toBeInTheDocument();

    // QR section
    expect(screen.getByText('https://registry.sih2026.edu/verify/REG-2026-A8F92D')).toBeInTheDocument();
    expect(screen.getByLabelText(/QR Verification Code/i)).toBeInTheDocument();

    // Verify on Public Portal link
    const verifyLink = screen.getByRole('link', { name: /verify on public portal/i });
    expect(verifyLink).toHaveAttribute('href', '/verify/REG-2026-A8F92D');
  });

  it('triggers PDF binary download when clicking Download Official PDF Certificate button', async () => {
    vi.mocked(certificateService.getCertificateMetadata).mockResolvedValueOnce(mockCertificateData);
    const mockBlob = new Blob(['%PDF-1.4 mock binary'], { type: 'application/pdf' });
    vi.mocked(certificateService.downloadCertificatePdf).mockResolvedValueOnce(mockBlob);

    render(
      <MemoryRouter initialEntries={['/certificates/REG-2026-A8F92D']}>
        <Routes>
          <Route path="/certificates/:registrationId" element={<CertificateDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    const downloadBtn = await screen.findByRole('button', { name: /download official pdf certificate/i });
    fireEvent.click(downloadBtn);

    await waitFor(() => {
      expect(certificateService.downloadCertificatePdf).toHaveBeenCalledWith('REG-2026-A8F92D');
    });

    expect(window.URL.createObjectURL).toHaveBeenCalledWith(mockBlob);
    expect(window.URL.revokeObjectURL).toHaveBeenCalledWith('blob:http://localhost/test-blob');
  });

  it('copies transaction hash, composite digest, IPFS CID, and verification URL to clipboard', async () => {
    vi.mocked(certificateService.getCertificateMetadata).mockResolvedValueOnce(mockCertificateData);

    render(
      <MemoryRouter initialEntries={['/certificates/REG-2026-A8F92D']}>
        <Routes>
          <Route path="/certificates/:registrationId" element={<CertificateDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    await screen.findByText(/REGISTRATION ID: REG-2026-A8F92D/i);

    // Copy transaction hash
    const copyTxBtn = screen.getByLabelText(/copy transaction hash/i);
    fireEvent.click(copyTxBtn);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      '0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb'
    );

    // Copy composite hash
    const copyDigestBtn = screen.getByLabelText(/copy composite hash/i);
    fireEvent.click(copyDigestBtn);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      'a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8'
    );

    // Copy IPFS CID
    const copyCidBtn = screen.getByLabelText(/copy ipfs cid/i);
    fireEvent.click(copyCidBtn);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      'bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi'
    );

    // Copy verification URL
    const copyUrlBtn = screen.getByRole('button', { name: /copy link/i });
    fireEvent.click(copyUrlBtn);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      'https://registry.sih2026.edu/verify/REG-2026-A8F92D'
    );
  });

  it('handles 404 not found error state with link to search portal', async () => {
    vi.mocked(certificateService.getCertificateMetadata).mockRejectedValueOnce({
      response: {
        status: 404,
        data: {
          error: {
            code: 'NOT_FOUND',
            message: 'Certificate registration ID not found.',
          },
        },
      },
    });

    render(
      <MemoryRouter initialEntries={['/certificates/REG-2026-NONEXIST']}>
        <Routes>
          <Route path="/certificates/:registrationId" element={<CertificateDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText('Certificate Not Found')).toBeInTheDocument();
    expect(screen.getByText(/We could not find an anchored certificate matching registration ID "REG-2026-NONEXIST"/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /search verification portal/i })).toBeInTheDocument();
  });

  it('handles 409 conflict state when version has active or upheld dispute', async () => {
    vi.mocked(certificateService.getCertificateMetadata).mockRejectedValueOnce({
      response: {
        status: 409,
        data: {
          error: {
            code: 'ACTIVE_DISPUTE_EXISTS',
            message: 'Cannot generate certificate for project version with an active dispute.',
          },
        },
      },
    });

    render(
      <MemoryRouter initialEntries={['/certificates/REG-2026-DISPUTED']}>
        <Routes>
          <Route path="/certificates/:registrationId" element={<CertificateDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText('Certificate Unavailable Due to Dispute')).toBeInTheDocument();
    expect(
      screen.getByText(/An ownership or plagiarism claim has been upheld or is under review for this project version/i)
    ).toBeInTheDocument();
  });
});
