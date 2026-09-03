import React from 'react';
import { ShieldCheck, GraduationCap, Building2, Mail, Hash } from 'lucide-react';
import { UserSummaryResponse } from '../../types';

export interface DashboardWelcomeProps {
  user: UserSummaryResponse | null;
}

export const DashboardWelcome: React.FC<DashboardWelcomeProps> = ({ user }) => {
  const displayName = user?.full_name || 'Student Researcher';
  const role = user?.role || 'STUDENT';
  const department = user?.department || 'Academic Research';
  const email = user?.email || '';
  const institutionId = user?.institution_id || '';

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800/80 p-6 sm:p-8 shadow-xl">
      {/* Background glow overlay */}
      <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 -ml-16 -mb-16 w-64 h-64 rounded-full bg-teal-500/10 blur-3xl pointer-events-none" />

      <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        {/* User Info & Greeting */}
        <div className="space-y-3 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Immutable Ownership Registry</span>
          </div>

          <div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Welcome back, <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-300">{displayName}</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Manage your academic intellectual assets, stage milestone version releases, and verify cryptographic blockchain proofs.
            </p>
          </div>

          {/* User metadata tags */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-emerald-400 font-mono font-semibold">
              <GraduationCap className="w-3.5 h-3.5" />
              {role}
            </span>

            {department && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300">
                <Building2 className="w-3.5 h-3.5 text-slate-400" />
                {department}
              </span>
            )}

            {institutionId && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300">
                <Hash className="w-3.5 h-3.5 text-slate-400" />
                {institutionId}
              </span>
            )}

            {email && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-400">
                <Mail className="w-3.5 h-3.5 text-slate-500" />
                {email}
              </span>
            )}
          </div>
        </div>

        {/* System Identifier Badge */}
        <div className="flex flex-col sm:flex-row md:flex-col items-start md:items-end justify-center gap-2 shrink-0 border-t md:border-t-0 md:border-l border-slate-800/80 pt-4 md:pt-0 md:pl-6">
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
            Registry Environment
          </div>
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950 border border-emerald-500/30 text-xs font-mono font-medium text-emerald-400 shadow-inner">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>SIH 2026 • EVM / IPFS</span>
          </div>
        </div>
      </div>
    </div>
  );
};
