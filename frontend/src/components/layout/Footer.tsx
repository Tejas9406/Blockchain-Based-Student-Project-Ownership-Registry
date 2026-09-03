import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-950/80 py-6 text-center text-xs text-slate-500">
      <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div>
          Blockchain-Based Student Project Ownership Registry • SIH 2026 CYB05
        </div>
        <div className="flex items-center gap-4 text-slate-400">
          <span>React 18 + Vite</span>
          <span>•</span>
          <span>FastAPI</span>
          <span>•</span>
          <span>EVM Smart Contracts</span>
          <span>•</span>
          <span>IPFS</span>
        </div>
      </div>
    </footer>
  );
};
