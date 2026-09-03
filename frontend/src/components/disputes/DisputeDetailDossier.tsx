import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FolderGit2,
  ShieldCheck,
  User,
  Calendar,
  Copy,
  Check,
  HardDrive,
  Link2,
  FileText,
  Award,
  Clock,
  ArrowLeft,
} from 'lucide-react';
import { DisputeDetailResponse } from '../../types';
import { ROUTES } from '../../constants/routes';
import { DisputeStatusBadge, DisputeTypeBadge } from './DisputeStatusBadge';

export interface DisputeDetailDossierProps {
  dispute: DisputeDetailResponse;
}

export const DisputeDetailDossier: React.FC<DisputeDetailDossierProps> = ({ dispute }) => {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const isResolved = dispute.status === 'RESOLVED' || dispute.status === 'REJECTED';

  return (
    <div
      data-testid="dispute-detail-dossier"
      className="p-6 sm:p-8 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-6"
    >
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="font-mono text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-lg">
              {dispute.public_id}
            </span>
            <DisputeTypeBadge type={dispute.dispute_type} />
            <DisputeStatusBadge status={dispute.status} />
          </div>

          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Ownership & Plagiarism Dispute Dossier
          </h2>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Link
            to={ROUTES.DISPUTES.LIST}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white bg-slate-850 border border-slate-800 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>All Claims</span>
          </Link>
        </div>
      </div>

      {/* Target Project Provenance Card */}
      <div className="p-4 sm:p-5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <FolderGit2 className="w-4 h-4 text-emerald-400" />
            <span>Disputed Project Record</span>
          </div>

          <div className="flex items-center gap-3 text-xs">
            {dispute.registration_id && (
              <Link
                to={ROUTES.VERIFICATION.DETAIL(dispute.registration_id)}
                className="inline-flex items-center gap-1 font-mono text-emerald-400 hover:text-emerald-300"
                title="View Public Verification Proof"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>{dispute.registration_id}</span>
              </Link>
            )}
            {dispute.project_public_id && (
              <Link
                to={ROUTES.PROJECTS.DETAIL(dispute.project_public_id)}
                className="text-slate-400 hover:text-white font-mono"
              >
                {dispute.project_public_id}
              </Link>
            )}
          </div>
        </div>

        <div>
          <h3 className="text-base font-bold text-white">
            {dispute.project_title || 'Target Project'}
          </h3>
        </div>
      </div>

      {/* Claimant Information & Timestamps */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Claimant Panel */}
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2 text-xs">
          <div className="flex items-center gap-2 font-semibold uppercase tracking-wider text-slate-400 text-[11px]">
            <User className="w-3.5 h-3.5 text-slate-500" />
            <span>Claimant Information</span>
          </div>
          {dispute.claimant ? (
            <div className="space-y-1">
              <p className="font-semibold text-white">{dispute.claimant.full_name}</p>
              <p className="font-mono text-slate-400">{dispute.claimant.public_id}</p>
              {dispute.claimant.institution_id && (
                <p className="text-slate-400">{dispute.claimant.institution_id}</p>
              )}
            </div>
          ) : (
            <p className="text-slate-500">Identity protected by registry privacy policy</p>
          )}
        </div>

        {/* Timestamps Panel */}
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2 text-xs">
          <div className="flex items-center gap-2 font-semibold uppercase tracking-wider text-slate-400 text-[11px]">
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <span>Lifecycle Timestamps</span>
          </div>
          <div className="space-y-1.5 font-mono">
            <div className="flex items-center justify-between text-slate-400">
              <span>Filed UTC:</span>
              <span className="text-slate-200">{formatDate(dispute.created_at)}</span>
            </div>
            {dispute.resolved_at && (
              <div className="flex items-center justify-between text-slate-400">
                <span>Adjudicated UTC:</span>
                <span className="text-emerald-400 font-semibold">{formatDate(dispute.resolved_at)}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Factual Claim Description */}
      <div className="p-4 sm:p-5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          <FileText className="w-4 h-4 text-amber-400" />
          <span>Factual Claim & Prior Art Assertion</span>
        </div>
        <p className="text-xs sm:text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
          {dispute.claim_description}
        </p>
      </div>

      {/* Evidence Section */}
      {dispute.evidence_url && (
        <div className="p-4 sm:p-5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-semibold uppercase tracking-wider text-slate-400 text-[11px]">
              <HardDrive className="w-4 h-4 text-sky-400" />
              <span>Prior Art Evidence Artifact (IPFS Manifest / URL)</span>
            </div>
            <button
              type="button"
              onClick={() => handleCopy(dispute.evidence_url!, 'evidence-url')}
              aria-label="Copy evidence URL"
              className="text-slate-400 hover:text-white"
            >
              {copiedKey === 'evidence-url' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
            </button>
          </div>
          <p className="font-mono text-sky-300 break-all bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
            {dispute.evidence_url}
          </p>
        </div>
      )}

      {/* On-Chain Cryptographic Proof (Read-Only) */}
      {dispute.transaction_hash && (
        <div className="p-4 sm:p-5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 text-xs font-mono">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-emerald-400 font-bold uppercase tracking-wider text-[11px]">
              <Link2 className="w-4 h-4" />
              <span>On-Chain Dispute Filing Transaction Hash</span>
            </div>
            <button
              type="button"
              onClick={() => handleCopy(dispute.transaction_hash!, 'tx-hash')}
              aria-label="Copy transaction hash"
              className="hover:text-white"
            >
              {copiedKey === 'tx-hash' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
            </button>
          </div>
          <p className="text-slate-300 truncate" title={dispute.transaction_hash}>
            {dispute.transaction_hash}
          </p>
        </div>
      )}

      {/* Adjudication Outcome Dossier */}
      {isResolved && (
        <div
          data-testid="adjudication-outcome"
          className={`p-5 rounded-xl border space-y-3 ${
            dispute.status === 'RESOLVED'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wider">
              <Award className="w-4 h-4" />
              <span>Authoritative Administrative Adjudication Result</span>
            </div>
            <DisputeStatusBadge status={dispute.status} />
          </div>

          {dispute.resolution_notes && (
            <div className="space-y-1 text-xs">
              <span className="text-slate-400 text-[11px] font-semibold uppercase">Resolution Rationale</span>
              <p className="text-slate-200 leading-relaxed bg-slate-950/50 p-3 rounded-lg border border-slate-800/80">
                {dispute.resolution_notes}
              </p>
            </div>
          )}

          {dispute.resolution_transaction_hash && (
            <div className="space-y-1 text-xs font-mono">
              <div className="flex items-center justify-between text-slate-400 text-[11px]">
                <span>On-Chain Resolution Transaction Hash</span>
                <button
                  type="button"
                  onClick={() => handleCopy(dispute.resolution_transaction_hash!, 'res-tx')}
                  aria-label="Copy resolution transaction hash"
                  className="hover:text-white"
                >
                  {copiedKey === 'res-tx' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
                </button>
              </div>
              <p className="text-slate-300 truncate" title={dispute.resolution_transaction_hash}>
                {dispute.resolution_transaction_hash}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Timeline Stepper */}
      <div className="pt-2 border-t border-slate-800/80 space-y-3">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Dispute Review Lifecycle
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800 space-y-1">
            <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
              <Check className="w-3.5 h-3.5" />
              <span>1. Claim Logged</span>
            </div>
            <p className="text-slate-400 text-[11px]">Evidence pinned to IPFS & anchored on EVM</p>
          </div>

          <div
            className={`p-3 rounded-xl border space-y-1 ${
              dispute.status === 'UNDER_REVIEW' || isResolved
                ? 'bg-slate-950/40 border-slate-800 text-slate-300'
                : 'bg-slate-950/20 border-slate-900 text-slate-600'
            }`}
          >
            <div
              className={`flex items-center gap-1.5 font-semibold ${
                dispute.status === 'UNDER_REVIEW' ? 'text-blue-400' : isResolved ? 'text-emerald-400' : 'text-slate-600'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              <span>2. Formal Review</span>
            </div>
            <p className="text-slate-400 text-[11px]">Institutional committee evaluates prior art</p>
          </div>

          <div
            className={`p-3 rounded-xl border space-y-1 ${
              isResolved
                ? dispute.status === 'RESOLVED'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                : 'bg-slate-950/20 border-slate-900 text-slate-600'
            }`}
          >
            <div
              className={`flex items-center gap-1.5 font-semibold ${
                isResolved
                  ? dispute.status === 'RESOLVED'
                    ? 'text-emerald-400'
                    : 'text-rose-400'
                  : 'text-slate-600'
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              <span>3. Adjudication</span>
            </div>
            <p className="text-slate-400 text-[11px]">Final outcome recorded permanently</p>
          </div>
        </div>
      </div>
    </div>
  );
};
