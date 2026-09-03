import React from 'react';
import {
  FolderPlus,
  GitBranch,
  FileCheck2,
  Cpu,
  Award,
} from 'lucide-react';

export const GettingStarted: React.FC = () => {
  const steps = [
    {
      step: '01',
      title: 'Project Setup',
      desc: 'Define title, abstract, department, and invite student team co-authors.',
      icon: FolderPlus,
    },
    {
      step: '02',
      title: 'Version Staging',
      desc: 'Tag milestone releases following standard Idea, Design, Prototype, or Final stages.',
      icon: GitBranch,
    },
    {
      step: '03',
      title: 'Artifact Intake',
      desc: 'Upload documentation, code archives, or CAD files with SHA-256 integrity hashes.',
      icon: FileCheck2,
    },
    {
      step: '04',
      title: 'Blockchain Anchor',
      desc: 'Relayer commits IPFS Root CID and deterministic composite hash to the EVM registry.',
      icon: Cpu,
    },
    {
      step: '05',
      title: 'Ownership Verification',
      desc: 'Download tamper-evident certificates with verifiable QR codes for institutional audits.',
      icon: Award,
    },
  ];

  return (
    <div className="p-6 sm:p-8 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h3 className="text-lg font-bold text-white tracking-tight">
            Academic Ownership Workflow
          </h3>
          <p className="text-xs sm:text-sm text-slate-400">
            How academic projects progress from local staging to cryptographic on-chain immutability.
          </p>
        </div>
        <span className="self-start sm:self-auto px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-slate-800 text-emerald-400 border border-slate-700">
          5-STEP VERIFIABLE PIPELINE
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {steps.map((item, index) => {
          const Icon = item.icon;
          return (
            <div
              key={item.step}
              className="relative flex flex-col justify-between p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-emerald-500/30 transition-colors group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-emerald-400">
                    STEP {item.step}
                  </span>
                  <div className="w-8 h-8 rounded-lg bg-slate-800/80 group-hover:bg-emerald-500/10 text-slate-300 group-hover:text-emerald-300 flex items-center justify-center transition-colors">
                    <Icon className="w-4 h-4" />
                  </div>
                </div>

                <div className="space-y-1">
                  <h4 className="text-xs sm:text-sm font-semibold text-white group-hover:text-emerald-300 transition-colors">
                    {item.title}
                  </h4>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    {item.desc}
                  </p>
                </div>
              </div>

              {index < steps.length - 1 && (
                <div className="hidden md:block absolute -right-2 top-1/2 -translate-y-1/2 z-10 text-slate-600 font-mono text-xs">
                  →
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
