import React from 'react';
import { Database, ShieldCheck, Cpu, Scale } from 'lucide-react';

export const DashboardOverview: React.FC = () => {
  const subsystems = [
    {
      title: 'Decentralized IPFS Storage',
      category: 'STORAGE LAYER',
      description:
        'Project artifacts are ingested into an IPFS node, calculating content-addressed root CIDs with strict SHA-256 cryptographic verification.',
      icon: Database,
    },
    {
      title: 'EVM Smart Contract Registry',
      category: 'IMMUTABLE ANCHOR',
      description:
        'ProjectRegistry.sol anchors project milestone hashes with immutable block timestamps, author wallets, and cryptographic proof verification.',
      icon: Cpu,
    },
    {
      title: 'Trustless Verification Engine',
      category: 'ZERO-TRUST VALIDATION',
      description:
        'Zero-dependency public verification enables evaluators, patent offices, and hackathons to confirm integrity by file or registration ID.',
      icon: ShieldCheck,
    },
    {
      title: 'Dispute & Resolution Protocol',
      category: 'GOVERNANCE & AUDIT',
      description:
        'Provides an on-chain transparent claim tracking mechanism with IPFS evidence dossier attachments and audit logs.',
      icon: Scale,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h3 className="text-lg font-bold text-white tracking-tight">
            Platform Architecture & Subsystems
          </h3>
          <p className="text-xs sm:text-sm text-slate-400">
            Cryptographic mechanisms ensuring non-repudiation and provenance for student research.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {subsystems.map((subsystem) => {
          const Icon = subsystem.icon;
          return (
            <div
              key={subsystem.title}
              className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800/80 hover:border-slate-700 transition-colors flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold tracking-wider text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                    {subsystem.category}
                  </span>
                  <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-300">
                    <Icon className="w-4 h-4" />
                  </div>
                </div>

                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-white">
                    {subsystem.title}
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {subsystem.description}
                  </p>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800/60 text-[11px] font-mono text-slate-500">
                // System Active
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
