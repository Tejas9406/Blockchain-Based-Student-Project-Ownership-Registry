import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, Database, Link2, CheckCircle2 } from 'lucide-react';
import { ROUTES } from '../../constants/routes';
import { verificationService } from '../../services/verification.service';
import { VerificationResponseData, NormalizedApiError } from '../../types';
import { normalizeApiError } from '../../utils/error';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { VerificationSearchForm } from '../../components/verification/VerificationSearchForm';
import { VerificationResultCard } from '../../components/verification/VerificationResultCard';

export const VerificationPortalPage: React.FC = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<NormalizedApiError | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerificationResponseData | null>(null);

  const handleVerifyRegistrationId = (registrationId: string) => {
    // Navigate directly to the public verification dossier URL
    navigate(ROUTES.VERIFICATION.DETAIL(registrationId));
  };

  const handleVerifyHash = async (hash: string, registrationId?: string) => {
    setIsLoading(true);
    setError(null);
    setVerificationResult(null);

    try {
      const result = await verificationService.verifyByHash({
        sha256_hash: hash,
        registration_id: registrationId,
      });
      setVerificationResult(result);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyFile = async (file: File, registrationId?: string) => {
    setIsLoading(true);
    setError(null);
    setVerificationResult(null);

    try {
      const result = await verificationService.verifyByFile(file, registrationId);
      setVerificationResult(result);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-4 px-4 sm:px-6">
      {/* Hero Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <ShieldCheck className="w-4 h-4" />
          <span>PUBLIC PROVENANCE PORTAL</span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Trustless Ownership Verification
        </h1>

        <p className="max-w-2xl mx-auto text-sm sm:text-base text-slate-400 leading-relaxed">
          Verify the authenticity, immutable timestamps, and EVM smart contract proofs of student academic projects registered across the national registry.
        </p>
      </div>

      {/* Error Banner */}
      {error && (
        <ErrorBanner
          error={error}
          onDismiss={() => setError(null)}
        />
      )}

      {/* Search / Ingestion Form */}
      <VerificationSearchForm
        isLoading={isLoading}
        onVerifyRegistrationId={handleVerifyRegistrationId}
        onVerifyHash={handleVerifyHash}
        onVerifyFile={handleVerifyFile}
      />

      {/* Inline Verification Result for Hash / File lookups */}
      {verificationResult && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white uppercase tracking-wider">
              Verification Result
            </h2>
            <button
              type="button"
              onClick={() => setVerificationResult(null)}
              className="text-xs text-slate-400 hover:text-white"
            >
              Clear Result
            </button>
          </div>

          <VerificationResultCard result={verificationResult} />
        </div>
      )}

      {/* Trust & Verification Architecture Architecture Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wide">
            <CheckCircle2 className="w-4 h-4" />
            <span>Deterministic SHA-256</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Every project version snapshot generates a deterministic composite Merkle hash of all project artifacts.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wide">
            <Link2 className="w-4 h-4" />
            <span>EVM On-Chain Anchoring</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Proofs are permanently anchored in the <code className="text-slate-300 font-mono">ProjectRegistry.sol</code> smart contract with block numbers and timestamps.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-sky-400 text-xs font-bold uppercase tracking-wide">
            <Database className="w-4 h-4" />
            <span>Decentralized IPFS</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Project code, documents, and assets are preserved as content-addressed IPFS UnixFS directories.
          </p>
        </div>
      </div>
    </div>
  );
};
