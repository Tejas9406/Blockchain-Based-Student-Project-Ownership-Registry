import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  Building,
  Copy,
  Check,
  HardDrive,
  Hash,
  Link2,
  FileCheck2,
  User,
  AlertTriangle,
  Award,
} from 'lucide-react';
import { VerificationResponseData } from '../../types';
import { ROUTES } from '../../constants/routes';
import { LifecycleBadge } from '../projects/ProjectStatusBadge';
import { VerificationStatusBadge } from './VerificationStatusBadge';

export interface VerificationResultCardProps {
  result: VerificationResponseData;
}

export const VerificationResultCard: React.FC<VerificationResultCardProps> = ({ result }) => {
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

  const {
    is_valid,
    registration_id,
    project,
    version,
    blockchain_proof,
    matched_hash,
    matched_file_name,
    verification_method,
    anchoring_status,
  } = result;

  const disputeStatus = blockchain_proof?.dispute_status || 'NONE';
  const isDisputed = disputeStatus !== 'NONE';

  return (
    <div
      data-testid="verification-result-card"
      className="p-6 sm:p-8 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-6"
    >
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2.5">
            {registration_id && (
              <span className="flex items-center gap-1.5 text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-lg">
                <ShieldCheck className="w-4 h-4" />
                <span>{registration_id}</span>
                <button
                  type="button"
                  onClick={() => handleCopy(registration_id, 'reg-id')}
                  aria-label="Copy registration ID"
                  className="hover:text-white transition-colors ml-1"
                  title="Copy Registration ID"
                >
                  {copiedKey === 'reg-id' ? (
                    <Check className="w-3.5 h-3.5 text-emerald-300" />
                  ) : (
                    <Copy className="w-3.5 h-3.5 text-emerald-500 hover:text-emerald-300" />
                  )}
                </button>
              </span>
            )}

            {verification_method && (
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                METHOD: {verification_method}
              </span>
            )}

            <VerificationStatusBadge
              isValid={is_valid}
              disputeStatus={disputeStatus}
              anchoringStatus={anchoring_status}
              matchConfirmed={blockchain_proof?.match_confirmed}
            />
          </div>

          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            {project?.title || 'Academic Project Ownership Dossier'}
          </h2>
        </div>

        {registration_id && is_valid && (
          <Link
            to={ROUTES.CERTIFICATES.DETAIL(registration_id)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-xs font-bold text-slate-950 transition-colors shadow-lg shadow-emerald-500/20 shrink-0 self-start sm:self-auto"
          >
            <Award className="w-4 h-4" />
            <span>View Certificate</span>
          </Link>
        )}
      </div>

      {/* Dispute Alert Banner if Disputed */}
      {isDisputed && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3 text-xs text-amber-200">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <p className="font-bold text-amber-300">Active Ownership Dispute Logged ({disputeStatus})</p>
            <p className="text-amber-200/80 leading-relaxed">
              This registered project milestone has an open ownership dispute claim undergoing administrative review. The on-chain cryptographic timestamp remains immutable while the dispute is pending.
            </p>
          </div>
        </div>
      )}

      {/* Matched Artifact Banner (if verified via Hash or File) */}
      {(matched_file_name || matched_hash) && (
        <div className="p-4 rounded-xl bg-sky-500/10 border border-sky-500/30 space-y-1 text-xs">
          <div className="flex items-center gap-2 text-sky-400 font-semibold">
            <FileCheck2 className="w-4 h-4" />
            <span>Direct File / Hash Match Confirmed</span>
          </div>
          {matched_file_name && (
            <p className="text-slate-300 font-mono">
              Matched File: <span className="text-white font-semibold">{matched_file_name}</span>
            </p>
          )}
          {matched_hash && (
            <div className="flex items-center gap-2 font-mono text-slate-400">
              <span className="truncate">Hash: {matched_hash}</span>
              <button
                type="button"
                onClick={() => handleCopy(matched_hash, 'match-hash')}
                aria-label="Copy matched hash"
                className="hover:text-white"
              >
                {copiedKey === 'match-hash' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Core Metadata Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Project Metadata */}
        {project && (
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              <Building className="w-4 h-4 text-slate-500" />
              <span>Project Provenance</span>
            </div>

            <div className="space-y-2 text-xs">
              <div>
                <span className="text-slate-500 text-[11px]">Title</span>
                <p className="font-semibold text-white text-sm">{project.title}</p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-slate-500 text-[11px]">Public ID</span>
                  <p className="font-mono text-slate-300">{project.public_id}</p>
                </div>
                <div>
                  <span className="text-slate-500 text-[11px]">Department</span>
                  <p className="text-slate-300 font-medium">{project.department}</p>
                </div>
              </div>

              {project.institution_name && (
                <div>
                  <span className="text-slate-500 text-[11px]">Institution</span>
                  <p className="text-slate-300 font-medium">{project.institution_name}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Version Milestone Metadata */}
        {version && (
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Version Milestone</span>
              </div>
              <LifecycleBadge stage={version.lifecycle_stage} />
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex items-center justify-between">
                <span className="text-slate-500 text-[11px]">Version Tag</span>
                <span className="text-white font-bold bg-slate-800 px-2 py-0.5 rounded text-xs">
                  {version.version_tag}
                </span>
              </div>

              {version.composite_sha256 && (
                <div className="space-y-0.5">
                  <div className="flex items-center justify-between text-slate-500 text-[11px]">
                    <div className="flex items-center gap-1">
                      <Hash className="w-3 h-3 text-emerald-400" />
                      <span>Composite SHA-256</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleCopy(version.composite_sha256!, 'ver-sha')}
                      aria-label="Copy composite SHA-256"
                      className="hover:text-white"
                    >
                      {copiedKey === 'ver-sha' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-500" />}
                    </button>
                  </div>
                  <p className="text-slate-300 truncate text-[11px]" title={version.composite_sha256}>
                    {version.composite_sha256}
                  </p>
                </div>
              )}

              {version.ipfs_root_cid && (
                <div className="space-y-0.5">
                  <div className="flex items-center justify-between text-slate-500 text-[11px]">
                    <div className="flex items-center gap-1">
                      <HardDrive className="w-3 h-3 text-sky-400" />
                      <span>IPFS Root CID</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleCopy(version.ipfs_root_cid!, 'ver-cid')}
                      aria-label="Copy IPFS Root CID"
                      className="hover:text-white"
                    >
                      {copiedKey === 'ver-cid' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-500" />}
                    </button>
                  </div>
                  <p className="text-sky-300 truncate text-[11px]" title={version.ipfs_root_cid}>
                    {version.ipfs_root_cid}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Authoritative On-Chain Blockchain Proof (Read-Only) */}
      {blockchain_proof && (
        <div className="p-5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Link2 className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                Authoritative On-Chain EVM Blockchain Proof
              </h3>
            </div>
            {blockchain_proof.network_name && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                NETWORK: {blockchain_proof.network_name}
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            {/* Transaction Hash */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-slate-500 text-[11px]">
                <span>Transaction Hash</span>
                <button
                  type="button"
                  onClick={() => handleCopy(blockchain_proof.transaction_hash, 'tx-hash')}
                  aria-label="Copy transaction hash"
                  className="hover:text-white"
                >
                  {copiedKey === 'tx-hash' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-500" />}
                </button>
              </div>
              <p className="text-slate-200 truncate" title={blockchain_proof.transaction_hash}>
                {blockchain_proof.transaction_hash}
              </p>
            </div>

            {/* Smart Contract Address */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-slate-500 text-[11px]">
                <span>Registry Smart Contract</span>
                <button
                  type="button"
                  onClick={() => handleCopy(blockchain_proof.smart_contract_address, 'contract-addr')}
                  aria-label="Copy contract address"
                  className="hover:text-white"
                >
                  {copiedKey === 'contract-addr' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-500" />}
                </button>
              </div>
              <p className="text-slate-200 truncate" title={blockchain_proof.smart_contract_address}>
                {blockchain_proof.smart_contract_address}
              </p>
            </div>

            {/* Author Wallet */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-slate-500 text-[11px]">
                <div className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  <span>Author Wallet Address</span>
                </div>
                <button
                  type="button"
                  onClick={() => handleCopy(blockchain_proof.author_wallet, 'author-wallet')}
                  aria-label="Copy author wallet address"
                  className="hover:text-white"
                >
                  {copiedKey === 'author-wallet' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-500" />}
                </button>
              </div>
              <p className="text-slate-200 truncate" title={blockchain_proof.author_wallet}>
                {blockchain_proof.author_wallet}
              </p>
            </div>

            {/* Block Number & Timestamp */}
            <div className="space-y-1">
              <span className="text-slate-500 text-[11px]">Block Number & Timestamp</span>
              <p className="text-slate-200">
                #{blockchain_proof.block_number} • {formatDate(blockchain_proof.block_timestamp)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Action Navigation Footer */}
      {is_valid && registration_id && (
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800 text-xs">
          <span className="text-slate-400">Official verified cryptographic registration</span>
          <Link
            to={ROUTES.CERTIFICATES.DETAIL(registration_id)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold transition-colors"
          >
            <Award className="w-4 h-4 text-amber-400" />
            <span>View Official Ownership Certificate</span>
          </Link>
        </div>
      )}
    </div>
  );
};
