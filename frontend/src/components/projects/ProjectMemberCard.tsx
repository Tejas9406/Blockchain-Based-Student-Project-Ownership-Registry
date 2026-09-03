import React, { useState } from 'react';
import {
  ShieldCheck,
  Crown,
  User,
  GraduationCap,
  Sparkles,
  Copy,
  Check,
  Calendar,
  Building,
} from 'lucide-react';
import { ProjectMemberItem, ProjectMemberRole } from '../../types';

export interface ProjectMemberRoleBadgeProps {
  role: ProjectMemberRole | string;
  className?: string;
}

export const ProjectMemberRoleBadge: React.FC<ProjectMemberRoleBadgeProps> = ({ role, className = '' }) => {
  switch (role) {
    case 'LEAD':
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30 ${className}`}
        >
          <Sparkles className="w-3 h-3 text-amber-400" />
          <span>Lead</span>
        </span>
      );
    case 'FACULTY_MENTOR':
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-500/10 text-purple-300 border border-purple-500/30 ${className}`}
        >
          <GraduationCap className="w-3 h-3 text-purple-400" />
          <span>Faculty Mentor</span>
        </span>
      );
    case 'CONTRIBUTOR':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-sky-500/10 text-sky-300 border border-sky-500/30 ${className}`}
        >
          <User className="w-3 h-3 text-sky-400" />
          <span>Contributor</span>
        </span>
      );
  }
};

export interface ProjectMemberCardProps {
  member: ProjectMemberItem;
}

export const ProjectMemberCard: React.FC<ProjectMemberCardProps> = ({ member }) => {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return 'Joined Initial';
    return new Date(isoString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getInitials = (name: string) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <div
      data-testid={`member-card-${member.user.public_id}`}
      className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800 hover:border-slate-700/80 shadow-md transition-all space-y-4 flex flex-col justify-between"
    >
      {/* Top Header: Avatar, Name, Owner Badge, Role */}
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            {/* Avatar Initials Bubble */}
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-xs shrink-0 ${
                member.is_owner
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : member.role_in_project === 'FACULTY_MENTOR'
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                  : 'bg-slate-800 text-slate-200 border border-slate-700'
              }`}
            >
              {getInitials(member.user.full_name)}
            </div>

            <div className="min-w-0 space-y-0.5">
              <div className="flex items-center gap-1.5 flex-wrap">
                <h4 className="text-sm font-bold text-white truncate" title={member.user.full_name}>
                  {member.user.full_name}
                </h4>
                {member.user.is_verified && (
                  <span title="Verified Institutional User">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  </span>
                )}
              </div>

              <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
                <span className="truncate max-w-[140px] sm:max-w-[180px]" title={member.user.email}>
                  {member.user.email}
                </span>
                <button
                  type="button"
                  onClick={() => handleCopy(member.user.email, `email-${member.user.public_id}`)}
                  aria-label="Copy member email"
                  className="hover:text-white"
                >
                  {copiedKey === `email-${member.user.public_id}` ? (
                    <Check className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <Copy className="w-3 h-3 text-slate-500 hover:text-slate-300" />
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end gap-1.5 shrink-0">
            {member.is_owner ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-extrabold bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm">
                <Crown className="w-3 h-3 text-amber-400" />
                <span>Primary Owner</span>
              </span>
            ) : (
              <ProjectMemberRoleBadge role={member.role_in_project} />
            )}
          </div>
        </div>

        {/* Department & Institution Info */}
        {(member.user.department || member.user.institution_id || member.user.institution_name) && (
          <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800/80 truncate">
            <Building className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span className="truncate">
              {[
                member.user.department,
                member.user.institution_name || member.user.institution_id,
              ]
                .filter(Boolean)
                .join(' • ')}
            </span>
          </div>
        )}
      </div>

      {/* Footer Meta: Contribution % & Joined Date */}
      <div className="flex items-center justify-between gap-2 pt-3 border-t border-slate-800/80 text-xs font-mono">
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500 text-[11px]">Contribution:</span>
          <span className="font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
            {(member.contribution_percentage ?? 0).toFixed(1)}%
          </span>
        </div>

        <div className="flex items-center gap-1 text-[11px] text-slate-500">
          <Calendar className="w-3 h-3" />
          <span>{formatDate(member.joined_at)}</span>
        </div>
      </div>
    </div>
  );
};
