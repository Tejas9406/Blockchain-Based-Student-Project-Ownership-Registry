import React, { useState } from 'react';
import { X, UserPlus, Mail, Percent, Sparkles, GraduationCap, User } from 'lucide-react';
import { projectService } from '../../services/project.service';
import {
  ProjectMemberCreateRequest,
  ProjectMemberItem,
  ProjectMemberRole,
  NormalizedApiError,
} from '../../types';
import { normalizeApiError } from '../../utils/error';
import { ErrorBanner } from '../ui/ErrorBanner';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export interface AddMemberModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newMember: ProjectMemberItem) => void;
}

const MEMBER_ROLES: { value: ProjectMemberRole; label: string; description: string; icon: React.FC<{ className?: string }> }[] = [
  {
    value: 'CONTRIBUTOR',
    label: 'Contributor',
    description: 'Active student co-author contributing code, documentation, or design.',
    icon: User,
  },
  {
    value: 'FACULTY_MENTOR',
    label: 'Faculty Mentor',
    description: 'Academic advisor supervising project milestones and methodology.',
    icon: GraduationCap,
  },
  {
    value: 'LEAD',
    label: 'Co-Lead',
    description: 'Project co-lead managing milestones and version deployments.',
    icon: Sparkles,
  },
];

export const AddMemberModal: React.FC<AddMemberModalProps> = ({
  projectId,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [identifier, setIdentifier] = useState('');
  const [role, setRole] = useState<ProjectMemberRole>('CONTRIBUTOR');
  const [contributionPercentage, setContributionPercentage] = useState<string>('0');

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<NormalizedApiError | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setError(null);

    const cleanIdentifier = identifier.trim();
    if (!cleanIdentifier) {
      setValidationError('Please provide a User Public ID (USR-YYYYMM-XXXXX) or Email address.');
      return;
    }

    const percentageNum = parseFloat(contributionPercentage);
    if (isNaN(percentageNum) || percentageNum < 0 || percentageNum > 100) {
      setValidationError('Contribution percentage must be a number between 0.00 and 100.00%.');
      return;
    }

    setIsLoading(true);

    try {
      const payload: ProjectMemberCreateRequest = {
        role_in_project: role,
        contribution_percentage: percentageNum,
      };

      // If matches user public id format or starts with USR-
      if (cleanIdentifier.toUpperCase().startsWith('USR-')) {
        payload.user_public_id = cleanIdentifier.toUpperCase();
      } else {
        payload.email = cleanIdentifier.toLowerCase();
      }

      const created = await projectService.addMember(projectId, payload);
      onSuccess(created);
      // Reset form
      setIdentifier('');
      setRole('CONTRIBUTOR');
      setContributionPercentage('0');
      onClose();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-member-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto"
    >
      <div className="relative w-full max-w-lg my-8 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <UserPlus className="w-5 h-5" />
            </div>
            <div>
              <h2 id="add-member-modal-title" className="text-lg font-bold text-white tracking-tight">
                Add Project Team Member
              </h2>
              <p className="text-xs text-slate-400">
                Invite or assign a verified student contributor or faculty mentor.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            aria-label="Close dialog"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="p-6 pb-0">
            <ErrorBanner error={error} onDismiss={() => setError(null)} />
          </div>
        )}

        {/* Modal Form */}
        <form noValidate onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* User Identifier Input */}
          <div className="space-y-1.5">
            <label
              htmlFor="member-identifier"
              className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400"
            >
              <Mail className="w-3.5 h-3.5 text-slate-500" />
              <span>User Public ID or Email Address</span>
            </label>
            <input
              id="member-identifier"
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="e.g. USR-202609-8F29A or student@sih2026.edu"
              disabled={isLoading}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs font-mono text-white placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 disabled:opacity-50"
            />
            <p className="text-[11px] text-slate-500">
              Target user must have an active registered account in the registry.
            </p>
          </div>

          {/* Project Member Role */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Assigned Project Role
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {MEMBER_ROLES.map((r) => {
                const IconComponent = r.icon;
                const isSelected = role === r.value;
                return (
                  <button
                    key={r.value}
                    type="button"
                    onClick={() => setRole(r.value)}
                    disabled={isLoading}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      isSelected
                        ? 'bg-emerald-500/10 border-emerald-500/40 text-white shadow-sm'
                        : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center gap-1.5">
                      <IconComponent className={`w-3.5 h-3.5 ${isSelected ? 'text-emerald-400' : 'text-slate-500'}`} />
                      <p className="font-semibold text-xs text-white">{r.label}</p>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-1 leading-snug">{r.description}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Contribution Percentage */}
          <div className="space-y-1.5">
            <label
              htmlFor="member-contribution"
              className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400"
            >
              <Percent className="w-3.5 h-3.5 text-slate-500" />
              <span>Declared Contribution Percentage (0 - 100%)</span>
            </label>
            <input
              id="member-contribution"
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={contributionPercentage}
              onChange={(e) => setContributionPercentage(e.target.value)}
              placeholder="e.g. 25.5"
              disabled={isLoading}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs font-mono text-white placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 disabled:opacity-50"
            />
          </div>

          {/* Validation Error */}
          {validationError && (
            <p className="text-xs font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-2 rounded-lg">
              {validationError}
            </p>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={isLoading}
              className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 disabled:text-slate-600 text-xs font-bold text-slate-950 transition-colors shadow-lg shadow-emerald-500/20 disabled:shadow-none"
            >
              {isLoading ? (
                <>
                  <LoadingSpinner size="sm" className="border-slate-950 border-t-transparent" />
                  <span>Adding Member...</span>
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  <span>Add Member</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
