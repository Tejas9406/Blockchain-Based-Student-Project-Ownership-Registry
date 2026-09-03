import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Calendar, User, ShieldCheck, FolderGit2 } from 'lucide-react';
import { DisputeDetailResponse } from '../../types';
import { ROUTES } from '../../constants/routes';
import { DisputeStatusBadge, DisputeTypeBadge } from './DisputeStatusBadge';

export interface DisputeCardProps {
  dispute: DisputeDetailResponse;
}

export const DisputeCard: React.FC<DisputeCardProps> = ({ dispute }) => {
  const formatDate = (isoString?: string | null) => {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div
      data-testid="dispute-card"
      className="p-5 sm:p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 shadow-lg transition-all space-y-4"
    >
      {/* Top Meta Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-lg">
            {dispute.public_id}
          </span>
          <DisputeTypeBadge type={dispute.dispute_type} />
          <DisputeStatusBadge status={dispute.status} />
        </div>

        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <Calendar className="w-3.5 h-3.5" />
          <span>Filed {formatDate(dispute.created_at)}</span>
        </div>
      </div>

      {/* Target Project Header */}
      <div className="space-y-1">
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <FolderGit2 className="w-3.5 h-3.5 text-slate-500" />
          <span>Target Project:</span>
          <span className="font-mono text-slate-300">{dispute.project_public_id}</span>
          {dispute.registration_id && (
            <span className="flex items-center gap-1 font-mono text-emerald-400 ml-2">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>{dispute.registration_id}</span>
            </span>
          )}
        </div>
        <h3 className="text-base font-bold text-white tracking-tight">
          {dispute.project_title || 'Target Project'}
        </h3>
      </div>

      {/* Claim Summary */}
      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
        {dispute.claim_description}
      </p>

      {/* Footer Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800/80 text-xs">
        {dispute.claimant ? (
          <div className="flex items-center gap-1.5 text-slate-400">
            <User className="w-3.5 h-3.5 text-slate-500" />
            <span>Claimant: <strong className="text-slate-200">{dispute.claimant.full_name}</strong></span>
            {dispute.claimant.institution_id && (
              <span className="text-slate-500">({dispute.claimant.institution_id})</span>
            )}
          </div>
        ) : (
          <span className="text-slate-500">Claimant details protected</span>
        )}

        <Link
          to={ROUTES.DISPUTES.DETAIL(dispute.public_id)}
          className="inline-flex items-center gap-1.5 font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
        >
          <span>View Dossier</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
