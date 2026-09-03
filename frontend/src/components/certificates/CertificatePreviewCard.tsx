import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Award,
  ShieldCheck,
  Download,
  ExternalLink,
  Copy,
  Check,
  QrCode,
  Users,
  Building,
  Calendar,
  Layers,
  HardDrive,
  Hash,
  Link2,
} from 'lucide-react';
import { CertificateMetadataData } from '../../types';
import { ROUTES } from '../../constants/routes';
import { certificateService } from '../../services/certificate.service';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export interface CertificatePreviewCardProps {
  certificate: CertificateMetadataData;
}

export const CertificatePreviewCard: React.FC<CertificatePreviewCardProps> = ({ certificate }) => {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleDownloadPdf = async () => {
    setIsDownloading(true);
    setDownloadError(null);

    try {
      const blob = await certificateService.downloadCertificatePdf(certificate.registration_id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ownership-certificate-${certificate.registration_id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch {
      setDownloadError('Unable to download PDF certificate. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return 'Pending Blockchain Finality';
    return new Date(isoString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZoneName: 'short',
    });
  };

  return (
    <div
      data-testid="certificate-preview-card"
      className="relative w-full max-w-4xl mx-auto rounded-3xl bg-slate-900/90 border-2 border-amber-500/30 shadow-2xl shadow-amber-500/5 p-6 sm:p-10 space-y-8 overflow-hidden"
    >
      {/* Decorative Gold Certificate Corner Badges */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-amber-500/10 via-transparent to-transparent pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-32 h-32 bg-gradient-to-tr from-amber-500/10 via-transparent to-transparent pointer-events-none" />

      {/* Top Formal Seal & Institution Header */}
      <div className="text-center space-y-3 border-b border-slate-800/80 pb-6">
        <div className="inline-flex p-3.5 rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-inner">
          <Award className="w-10 h-10" />
        </div>

        <div className="space-y-1">
          <p className="text-xs font-bold tracking-widest text-amber-400 uppercase">
            National Student Project Ownership Registry
          </p>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Certificate of Project Ownership & Provenance
          </h1>
          <p className="text-xs text-slate-400 max-w-lg mx-auto">
            Official immutable cryptographic proof anchored on the Ethereum Virtual Machine blockchain.
          </p>
        </div>

        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-950 border border-amber-500/30 text-xs font-mono font-bold text-amber-300">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>REGISTRATION ID: {certificate.registration_id}</span>
        </div>
      </div>

      {/* Certificate Main Body */}
      <div className="space-y-6 text-center">
        <p className="text-xs uppercase tracking-widest text-slate-400 font-semibold">
          This certifies that the academic project
        </p>

        <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight text-balance">
          {certificate.project_title}
        </h2>

        <div className="flex flex-wrap items-center justify-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800 text-xs font-mono font-bold text-slate-200 border border-slate-700">
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
            <span>Version {certificate.version_tag}</span>
          </span>

          {certificate.lifecycle_stage && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800 text-xs font-semibold text-slate-300 border border-slate-700">
              <span>Stage: {certificate.lifecycle_stage}</span>
            </span>
          )}

          {certificate.department && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800 text-xs text-slate-300 border border-slate-700">
              <Building className="w-3.5 h-3.5 text-slate-500" />
              <span>{certificate.department}</span>
            </span>
          )}
        </div>

        <p className="text-xs uppercase tracking-widest text-slate-400 font-semibold pt-2">
          Has been registered by verified student author(s)
        </p>

        {/* Authors List */}
        <div className="flex flex-wrap items-center justify-center gap-2.5">
          {certificate.authors && certificate.authors.length > 0 ? (
            certificate.authors.map((author, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-slate-950/80 border border-slate-700/80 text-xs font-bold text-white shadow-sm"
              >
                <Users className="w-3.5 h-3.5 text-amber-400" />
                <span>{author}</span>
              </span>
            ))
          ) : (
            <span className="text-xs text-slate-400">Verified Project Contributor</span>
          )}
        </div>

        <p className="text-xs text-slate-400">
          Affiliated with <strong className="text-slate-200">{certificate.institution || 'Academic Institution'}</strong>
        </p>
      </div>

      {/* Cryptographic & On-Chain Proof Dossier */}
      <div className="p-5 sm:p-6 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-4 text-xs font-mono">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
          <div className="flex items-center gap-2 text-emerald-400 font-bold uppercase tracking-wider text-[11px]">
            <ShieldCheck className="w-4 h-4" />
            <span>Immutable On-Chain Verification Proof</span>
          </div>
          <div className="flex items-center gap-1 text-[11px] text-slate-400">
            <Calendar className="w-3.5 h-3.5" />
            <span>Anchored: {formatDate(certificate.anchored_timestamp)}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Transaction Hash */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-slate-500 text-[11px]">
              <span className="flex items-center gap-1">
                <Link2 className="w-3 h-3 text-slate-400" />
                <span>Transaction Hash</span>
              </span>
              <button
                type="button"
                onClick={() => handleCopy(certificate.transaction_hash, 'tx-hash')}
                aria-label="Copy transaction hash"
                className="hover:text-white"
              >
                {copiedKey === 'tx-hash' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
            <p className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 truncate" title={certificate.transaction_hash}>
              {certificate.transaction_hash}
            </p>
          </div>

          {/* Composite SHA-256 Hash */}
          {certificate.composite_sha256 && (
            <div className="space-y-1">
              <div className="flex items-center justify-between text-slate-500 text-[11px]">
                <span className="flex items-center gap-1">
                  <Hash className="w-3 h-3 text-slate-400" />
                  <span>Composite Digest</span>
                </span>
                <button
                  type="button"
                  onClick={() => handleCopy(certificate.composite_sha256!, 'composite-hash')}
                  aria-label="Copy composite hash"
                  className="hover:text-white"
                >
                  {copiedKey === 'composite-hash' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
              <p className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 truncate" title={certificate.composite_sha256}>
                {certificate.composite_sha256}
              </p>
            </div>
          )}

          {/* IPFS Root CID */}
          {certificate.ipfs_root_cid && (
            <div className="space-y-1">
              <div className="flex items-center justify-between text-slate-500 text-[11px]">
                <span className="flex items-center gap-1">
                  <HardDrive className="w-3 h-3 text-slate-400" />
                  <span>IPFS Root CID</span>
                </span>
                <button
                  type="button"
                  onClick={() => handleCopy(certificate.ipfs_root_cid!, 'ipfs-cid')}
                  aria-label="Copy IPFS CID"
                  className="hover:text-white"
                >
                  {copiedKey === 'ipfs-cid' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
              <p className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-sky-300 truncate" title={certificate.ipfs_root_cid}>
                {certificate.ipfs_root_cid}
              </p>
            </div>
          )}

          {/* Block Number & Dispute Standing */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-slate-500 text-[11px]">
              <span>Block Confirmation & Standing</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between text-slate-300">
              <span>Block #{certificate.block_number ?? 'Confirmed'}</span>
              <span className="text-emerald-400 font-bold">Clean Standing</span>
            </div>
          </div>
        </div>
      </div>

      {/* QR Code Verification Section */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-6 p-5 rounded-2xl bg-slate-950/60 border border-slate-800">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-white rounded-xl shadow-md text-slate-900 shrink-0">
            <QrCode className="w-12 h-12" aria-label="QR Verification Code" />
          </div>
          <div className="space-y-1">
            <h4 className="text-xs font-bold uppercase tracking-wider text-white">
              Scan QR to Verify Authenticity
            </h4>
            <p className="text-xs text-slate-400">
              Direct link to cryptographic verification portal:
            </p>
            <p className="text-[11px] font-mono text-emerald-400 break-all">
              {certificate.verification_url}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-stretch sm:self-auto justify-end">
          <button
            type="button"
            onClick={() => handleCopy(certificate.verification_url, 'verify-url')}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition-colors"
          >
            {copiedKey === 'verify-url' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>Copy Link</span>
          </button>
        </div>
      </div>

      {/* Download Error Banner */}
      {downloadError && (
        <p className="text-xs font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-4 py-2.5 rounded-xl text-center">
          {downloadError}
        </p>
      )}

      {/* Footer Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-800">
        <Link
          to={ROUTES.VERIFICATION.DETAIL(certificate.registration_id)}
          className="inline-flex items-center gap-2 text-xs font-bold text-emerald-400 hover:text-emerald-300 transition-colors"
        >
          <ExternalLink className="w-4 h-4" />
          <span>Verify on Public Portal</span>
        </Link>

        <button
          type="button"
          onClick={handleDownloadPdf}
          disabled={isDownloading}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:bg-slate-800 disabled:text-slate-600 text-xs font-bold text-slate-950 transition-colors shadow-lg shadow-amber-500/20 disabled:shadow-none"
        >
          {isDownloading ? (
            <>
              <LoadingSpinner size="sm" className="border-slate-950 border-t-transparent" />
              <span>Generating PDF...</span>
            </>
          ) : (
            <>
              <Download className="w-4 h-4" />
              <span>Download Official PDF Certificate</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
