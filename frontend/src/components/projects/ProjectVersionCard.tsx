import React, { useState } from 'react';
import {
  Layers,
  Calendar,
  Copy,
  Check,
  FileCode,
  FileText,
  FileCheck,
  ChevronDown,
  ChevronUp,
  Link2,
  HardDrive,
  ShieldCheck,
  Hash,
} from 'lucide-react';
import { ProjectVersionDetail } from '../../types';
import { LifecycleBadge, AnchoringBadge } from './ProjectStatusBadge';

export interface ProjectVersionCardProps {
  version: ProjectVersionDetail;
  isExpandedDefault?: boolean;
}

export const ProjectVersionCard: React.FC<ProjectVersionCardProps> = ({
  version,
  isExpandedDefault = false,
}) => {
  const [isArtifactsOpen, setIsArtifactsOpen] = useState(isExpandedDefault);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const formatDate = (isoString?: string) => {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatBytes = (bytes?: number) => {
    if (bytes === undefined || bytes === null || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const artifacts = version.artifacts || [];

  return (
    <div
      data-testid={`version-card-${version.public_id}`}
      className="p-5 sm:p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg space-y-4 hover:border-slate-700/80 transition-all duration-200"
    >
      {/* Top Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="flex items-center gap-1.5 text-xs font-mono font-bold text-white bg-slate-800 border border-slate-700 px-2.5 py-1 rounded-lg">
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
            <span>{version.version_tag}</span>
            <span className="text-slate-400 font-normal">#{version.version_index}</span>
          </span>

          <LifecycleBadge stage={version.lifecycle_stage} />
          <AnchoringBadge status={version.anchoring_status} />

          {version.registration_id && (
            <span className="inline-flex items-center gap-1 text-xs font-mono font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">
              <ShieldCheck className="w-3 h-3" />
              <span>{version.registration_id}</span>
              <button
                type="button"
                onClick={() => handleCopy(version.registration_id!, `reg-${version.public_id}`)}
                aria-label="Copy registration ID"
                className="hover:text-white transition-colors ml-0.5"
                title="Copy Registration ID"
              >
                {copiedKey === `reg-${version.public_id}` ? (
                  <Check className="w-3 h-3 text-emerald-300" />
                ) : (
                  <Copy className="w-3 h-3 text-emerald-500 hover:text-emerald-300" />
                )}
              </button>
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 shrink-0">
          <Calendar className="w-3.5 h-3.5 text-slate-500" />
          <span>{formatDate(version.created_at)}</span>
        </div>
      </div>

      {/* Version Title & Description */}
      <div className="space-y-1.5">
        <h3 className="text-lg font-bold text-white tracking-tight">{version.title}</h3>
        {version.description && (
          <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-xl border border-slate-800/60">
            {version.description}
          </p>
        )}
      </div>

      {/* Cryptographic & Storage Identifiers Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
        {/* Composite SHA-256 Digest */}
        {version.composite_sha256 && (
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
              <div className="flex items-center gap-1.5">
                <Hash className="w-3.5 h-3.5 text-emerald-400" />
                <span>Deterministic Composite SHA-256</span>
              </div>
              <button
                type="button"
                onClick={() => handleCopy(version.composite_sha256!, `sha-${version.public_id}`)}
                aria-label="Copy Composite SHA-256"
                className="hover:text-white transition-colors"
                title="Copy SHA-256 Hash"
              >
                {copiedKey === `sha-${version.public_id}` ? (
                  <Check className="w-3 h-3 text-emerald-400" />
                ) : (
                  <Copy className="w-3 h-3 text-slate-500 hover:text-slate-300" />
                )}
              </button>
            </div>
            <p className="text-slate-300 truncate font-mono text-[11px]" title={version.composite_sha256}>
              {version.composite_sha256}
            </p>
          </div>
        )}

        {/* IPFS Root CID */}
        {version.ipfs_root_cid && (
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-[11px] font-medium">
              <div className="flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5 text-sky-400" />
                <span>IPFS Root Directory CID</span>
              </div>
              <button
                type="button"
                onClick={() => handleCopy(version.ipfs_root_cid!, `cid-${version.public_id}`)}
                aria-label="Copy IPFS Root CID"
                className="hover:text-white transition-colors"
                title="Copy IPFS Root CID"
              >
                {copiedKey === `cid-${version.public_id}` ? (
                  <Check className="w-3 h-3 text-emerald-400" />
                ) : (
                  <Copy className="w-3 h-3 text-slate-500 hover:text-slate-300" />
                )}
              </button>
            </div>
            <p className="text-sky-300 truncate font-mono text-[11px]" title={version.ipfs_root_cid}>
              {version.ipfs_root_cid}
            </p>
          </div>
        )}
      </div>

      {/* On-Chain Blockchain Proof Summary (Read-Only) */}
      {version.blockchain_record && (
        <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/90 space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
            <Link2 className="w-3.5 h-3.5" />
            <span>On-Chain Blockchain Record Proof</span>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 border border-slate-700 ml-1">
              {version.blockchain_record.network_name || 'EVM'}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono text-slate-400">
            <div className="space-y-0.5">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider">Transaction Hash</span>
              <div className="flex items-center gap-1">
                <span className="text-slate-300 truncate text-[11px]" title={version.blockchain_record.transaction_hash}>
                  {version.blockchain_record.transaction_hash}
                </span>
                <button
                  type="button"
                  onClick={() => handleCopy(version.blockchain_record!.transaction_hash, `tx-${version.public_id}`)}
                  aria-label="Copy transaction hash"
                  className="hover:text-white transition-colors shrink-0"
                >
                  {copiedKey === `tx-${version.public_id}` ? (
                    <Check className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <Copy className="w-3 h-3 text-slate-500 hover:text-slate-300" />
                  )}
                </button>
              </div>
            </div>

            {version.blockchain_record.block_number !== undefined && (
              <div className="space-y-0.5">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider">Block Number</span>
                <p className="text-slate-300 font-semibold text-[11px]">
                  #{version.blockchain_record.block_number}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Associated Artifacts Accordion */}
      <div className="border-t border-slate-800/80 pt-3">
        <button
          type="button"
          onClick={() => setIsArtifactsOpen((prev) => !prev)}
          aria-expanded={isArtifactsOpen}
          className="w-full flex items-center justify-between text-xs font-semibold text-slate-400 hover:text-white py-1 transition-colors"
        >
          <div className="flex items-center gap-2">
            <FileCode className="w-4 h-4 text-slate-500" />
            <span>Associated Artifacts ({artifacts.length})</span>
          </div>
          {isArtifactsOpen ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </button>

        {isArtifactsOpen && (
          <div className="mt-3 space-y-2">
            {artifacts.length === 0 ? (
              <p className="text-xs text-slate-500 italic p-3 rounded-lg bg-slate-950/30 text-center">
                No artifacts attached to this milestone snapshot.
              </p>
            ) : (
              artifacts.map((art) => (
                <div
                  key={art.public_id}
                  className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/70 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-7 h-7 rounded-lg bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-400 shrink-0">
                      {art.artifact_category === 'SOURCE_CODE' ? (
                        <FileCode className="w-3.5 h-3.5 text-blue-400" />
                      ) : art.artifact_category === 'DOCUMENTATION' ? (
                        <FileText className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <FileCheck className="w-3.5 h-3.5 text-amber-400" />
                      )}
                    </div>

                    <div className="min-w-0 space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white truncate max-w-xs">{art.file_name}</span>
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                          {art.artifact_category}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-[11px] font-mono text-slate-500">
                        <span>{art.public_id}</span>
                        <span>•</span>
                        <span>{formatBytes(art.file_size_bytes)}</span>
                      </div>
                    </div>
                  </div>

                  {art.sha256_hash && (
                    <div className="flex items-center gap-1.5 font-mono text-[11px] text-slate-400 shrink-0 self-start sm:self-auto">
                      <span className="text-slate-500 truncate max-w-[120px]" title={art.sha256_hash}>
                        {art.sha256_hash.slice(0, 10)}...
                      </span>
                      <button
                        type="button"
                        onClick={() => handleCopy(art.sha256_hash, `art-${art.public_id}`)}
                        aria-label="Copy artifact SHA-256"
                        className="hover:text-white transition-colors"
                        title="Copy SHA-256"
                      >
                        {copiedKey === `art-${art.public_id}` ? (
                          <Check className="w-3 h-3 text-emerald-400" />
                        ) : (
                          <Copy className="w-3 h-3 text-slate-600 hover:text-slate-400" />
                        )}
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};
