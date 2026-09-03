import React from 'react';
import { CheckCircle, AlertTriangle, XCircle, Clock } from 'lucide-react';
import { DisputeStatus } from '../../types';

export interface VerificationStatusBadgeProps {
  isValid: boolean;
  disputeStatus?: DisputeStatus | string;
  anchoringStatus?: string | null;
  matchConfirmed?: boolean;
  className?: string;
}

export const VerificationStatusBadge: React.FC<VerificationStatusBadgeProps> = ({
  isValid,
  disputeStatus = 'NONE',
  anchoringStatus,
  matchConfirmed = true,
  className = '',
}) => {
  const isDisputed = disputeStatus && disputeStatus !== 'NONE';

  if (!isValid || matchConfirmed === false) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 ${className}`}
      >
        <XCircle className="w-3.5 h-3.5 text-rose-400" />
        <span>Verification Failed</span>
      </span>
    );
  }

  if (isDisputed) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 ${className}`}
      >
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
        <span>Under Dispute ({disputeStatus})</span>
      </span>
    );
  }

  if (anchoringStatus && anchoringStatus !== 'ANCHORED') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30 ${className}`}
      >
        <Clock className="w-3.5 h-3.5 text-blue-400" />
        <span>Anchoring State ({anchoringStatus})</span>
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 ${className}`}
    >
      <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
      <span>Valid Ownership Proof</span>
    </span>
  );
};
