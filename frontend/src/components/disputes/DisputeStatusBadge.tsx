import React from 'react';
import { AlertTriangle, Clock, CheckCircle2, XCircle, FileWarning } from 'lucide-react';
import { DisputeStatus, DisputeType } from '../../types';

export interface DisputeStatusBadgeProps {
  status: DisputeStatus | string;
  className?: string;
}

export const DisputeStatusBadge: React.FC<DisputeStatusBadgeProps> = ({ status, className = '' }) => {
  switch (status) {
    case 'OPEN':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 ${className}`}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          <span>Open Claim</span>
        </span>
      );
    case 'UNDER_REVIEW':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30 ${className}`}
        >
          <Clock className="w-3.5 h-3.5 text-blue-400" />
          <span>Under Review</span>
        </span>
      );
    case 'RESOLVED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 ${className}`}
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Resolved (Claim Upheld)</span>
        </span>
      );
    case 'REJECTED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 ${className}`}
        >
          <XCircle className="w-3.5 h-3.5 text-rose-400" />
          <span>Rejected (Claim Dismissed)</span>
        </span>
      );
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700 ${className}`}
        >
          <span>{status}</span>
        </span>
      );
  }
};

export interface DisputeTypeBadgeProps {
  type: DisputeType | string;
  className?: string;
}

export const DisputeTypeBadge: React.FC<DisputeTypeBadgeProps> = ({ type, className = '' }) => {
  switch (type) {
    case 'PLAGIARISM':
      return (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-300 border border-rose-500/20 ${className}`}
        >
          <FileWarning className="w-3 h-3" />
          <span>Plagiarism</span>
        </span>
      );
    case 'UNAUTHORIZED_USE':
      return (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/20 ${className}`}
        >
          <FileWarning className="w-3 h-3" />
          <span>Unauthorized Use</span>
        </span>
      );
    case 'CITATION_FAILURE':
      return (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/20 ${className}`}
        >
          <FileWarning className="w-3 h-3" />
          <span>Citation Failure</span>
        </span>
      );
    case 'OTHER':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-300 border border-slate-700 ${className}`}
        >
          <FileWarning className="w-3 h-3" />
          <span>{type}</span>
        </span>
      );
  }
};
