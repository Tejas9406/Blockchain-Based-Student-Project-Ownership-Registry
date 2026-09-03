import React from 'react';
import {
  LifecycleStage,
  ProjectStatus,
  AnchoringStatus,
} from '../../types';

export interface LifecycleBadgeProps {
  stage: LifecycleStage;
  className?: string;
}

export const LifecycleBadge: React.FC<LifecycleBadgeProps> = ({ stage, className = '' }) => {
  const styles: Record<LifecycleStage, string> = {
    IDEA: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    DESIGN: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
    PROTOTYPE: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    FINAL: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${styles[stage] || 'bg-slate-800 text-slate-300 border-slate-700'} ${className}`}
    >
      {stage}
    </span>
  );
};

export interface StatusBadgeProps {
  status: ProjectStatus;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const styles: Record<ProjectStatus, string> = {
    ACTIVE: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    ARCHIVED: 'bg-slate-700/30 text-slate-400 border-slate-700/50',
    UNDER_DISPUTE: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  };

  const labels: Record<ProjectStatus, string> = {
    ACTIVE: 'Active',
    ARCHIVED: 'Archived',
    UNDER_DISPUTE: 'Under Dispute',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[status] || 'bg-slate-800 text-slate-300 border-slate-700'} ${className}`}
    >
      {labels[status] || status}
    </span>
  );
};

export interface VisibilityBadgeProps {
  visibility: 'PUBLIC' | 'INSTITUTIONAL' | 'PRIVATE';
  className?: string;
}

export const VisibilityBadge: React.FC<VisibilityBadgeProps> = ({ visibility, className = '' }) => {
  const styles = {
    PUBLIC: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    INSTITUTIONAL: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    PRIVATE: 'bg-slate-700/30 text-slate-400 border-slate-700/50',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium border ${styles[visibility] || 'bg-slate-800 text-slate-300 border-slate-700'} ${className}`}
    >
      {visibility}
    </span>
  );
};

export interface AnchoringBadgeProps {
  status: AnchoringStatus;
  className?: string;
}

export const AnchoringBadge: React.FC<AnchoringBadgeProps> = ({ status, className = '' }) => {
  const styles: Record<AnchoringStatus, string> = {
    DRAFT: 'bg-slate-800 text-slate-400 border-slate-700',
    PENDING: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    ANCHORING: 'bg-blue-500/10 text-blue-400 border-blue-500/20 animate-pulse',
    ANCHORED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    FAILED: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  };

  const labels: Record<AnchoringStatus, string> = {
    DRAFT: 'Draft',
    PENDING: 'Pending',
    ANCHORING: 'Anchoring',
    ANCHORED: 'Anchored',
    FAILED: 'Failed',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${styles[status] || 'bg-slate-800 text-slate-300 border-slate-700'} ${className}`}
    >
      {labels[status] || status}
    </span>
  );
};
