import { useEffect, useState } from 'react';
import { ShieldCheck, Server, Blocks, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { API_BASE_URL, checkBackendHealth, HealthCheckResponse } from './services/api';

export function App() {
  const [backendHealth, setBackendHealth] = useState<HealthCheckResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await checkBackendHealth();
      setBackendHealth(data);
    } catch (err: any) {
      setError(err.message || 'Unable to connect to backend service.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center shadow-lg shadow-emerald-950/40">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white">Student Project Ownership Registry</h1>
              <p className="text-xs text-emerald-400 font-medium">Smart India Hackathon 2026 • Problem Statement CYB05</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/70 border border-emerald-500/30 text-emerald-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Phase 0: Environment Active
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-12 flex-1 flex flex-col justify-center">
        <div className="text-center space-y-4 mb-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300 shadow-inner">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Dev Environment Foundation Initialized</span>
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight text-white">
            Frontend environment is working.
          </h2>
          <p className="max-w-2xl mx-auto text-slate-400 text-sm md:text-base leading-relaxed">
            Welcome to the 3-developer monorepo foundation. Business modules (Authentication, Project Registry, IPFS Storage, Blockchain Anchoring, Verification) are isolated and prepared for upcoming development phases.
          </p>
        </div>

        {/* Diagnostic Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          {/* Frontend Module Card */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <span className="text-xs font-mono text-emerald-400 bg-emerald-950/50 px-2 py-0.5 rounded-md border border-emerald-800/40">Healthy</span>
            </div>
            <h3 className="text-base font-semibold text-white mb-1">Developer 1: Frontend</h3>
            <p className="text-xs text-slate-400 mb-4">React 18 + Vite + TypeScript + Tailwind CSS</p>
            <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80 font-mono text-xs text-slate-300">
              <div className="text-slate-400 text-[10px] uppercase font-semibold">API Base URL</div>
              <div className="truncate text-blue-300">{API_BASE_URL}</div>
            </div>
          </div>

          {/* Backend Module Card */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <Server className="w-5 h-5" />
              </div>
              <span className={`text-xs font-mono px-2 py-0.5 rounded-md border ${backendHealth ? 'text-emerald-400 bg-emerald-950/50 border-emerald-800/40' : 'text-amber-400 bg-amber-950/50 border-amber-800/40'}`}>
                {backendHealth ? 'Connected' : 'Standby / Local'}
              </span>
            </div>
            <h3 className="text-base font-semibold text-white mb-1">Developer 2: Backend</h3>
            <p className="text-xs text-slate-400 mb-4">FastAPI + Python + PostgreSQL</p>
            <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80 font-mono text-xs text-slate-300 flex items-center justify-between">
              <div>
                <div className="text-slate-400 text-[10px] uppercase font-semibold">Health Status</div>
                <div className="text-emerald-300">{backendHealth ? `${backendHealth.status} (${backendHealth.service})` : (error ? 'Offline' : 'Checking...')}</div>
              </div>
              <button 
                onClick={fetchHealth} 
                disabled={isLoading}
                aria-label="Refresh backend health status"
                className="p-1.5 hover:bg-slate-800 rounded-md transition-colors text-slate-400 hover:text-slate-200"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Blockchain Module Card */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                <Blocks className="w-5 h-5" />
              </div>
              <span className="text-xs font-mono text-purple-300 bg-purple-950/50 px-2 py-0.5 rounded-md border border-purple-800/40">Ready</span>
            </div>
            <h3 className="text-base font-semibold text-white mb-1">Developer 3: Blockchain</h3>
            <p className="text-xs text-slate-400 mb-4">Solidity 0.8.24 + Hardhat + EVM</p>
            <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80 font-mono text-xs text-slate-300">
              <div className="text-slate-400 text-[10px] uppercase font-semibold">Network Target</div>
              <div className="text-purple-300">Hardhat Local (ChainID: 31337)</div>
            </div>
          </div>
        </div>

        {/* Notice Banner */}
        <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
          <div className="text-xs text-slate-400 leading-relaxed">
            <span className="font-semibold text-slate-300">Phase 0 Guardrail:</span> Business features (Authentication, Registration, File Upload, IPFS Services, Smart Contract Ownership Proofs, QR Generation) are strictly deferred to subsequent development phases.
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-400">
        Blockchain-Based Student Project Ownership Registry • SIH 2026 CYB05 Monorepo
      </footer>
    </div>
  );
}

export default App;
