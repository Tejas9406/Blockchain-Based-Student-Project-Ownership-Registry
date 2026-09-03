import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ShieldCheck, ArrowLeft, RefreshCw, AlertCircle } from 'lucide-react';
import { ROUTES } from '../../constants/routes';
import { verificationService } from '../../services/verification.service';
import { VerificationResponseData, NormalizedApiError } from '../../types';
import { normalizeApiError } from '../../utils/error';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { VerificationResultCard } from '../../components/verification/VerificationResultCard';

export const VerificationDetailPage: React.FC = () => {
  const { registrationId } = useParams<{ registrationId: string }>();

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<NormalizedApiError | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerificationResponseData | null>(null);

  const fetchVerification = useCallback(async () => {
    if (!registrationId) {
      setError({
        status: 400,
        code: 'VALIDATION_ERROR',
        message: 'No registration ID provided in URL path.',
      });
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await verificationService.verifyByRegistrationId(registrationId);
      setVerificationResult(data);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [registrationId]);

  useEffect(() => {
    fetchVerification();
  }, [fetchVerification]);

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-4 px-4 sm:px-6">
      {/* Navigation Top Bar */}
      <div className="flex items-center justify-between gap-4">
        <Link
          to={ROUTES.VERIFICATION.PORTAL}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Verification Portal</span>
        </Link>

        <button
          type="button"
          onClick={fetchVerification}
          disabled={isLoading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white bg-slate-900 border border-slate-800 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Re-verify</span>
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div
          data-testid="verification-loading"
          className="p-12 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col items-center justify-center text-center space-y-4"
        >
          <LoadingSpinner size="lg" />
          <div className="space-y-1">
            <h2 className="text-base font-bold text-white">Verifying Ownership Proof</h2>
            <p className="text-xs text-slate-400">
              Querying decentralized registry and EVM smart contract for registration{' '}
              <span className="font-mono text-emerald-400 font-bold">{registrationId}</span>...
            </p>
          </div>
        </div>
      )}

      {/* Error / Not Found State */}
      {!isLoading && error && (
        <div className="space-y-6">
          <ErrorBanner error={error} onDismiss={() => setError(null)} />

          <div className="p-8 rounded-2xl bg-slate-900/60 border border-rose-900/30 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto text-rose-400">
              <AlertCircle className="w-6 h-6" />
            </div>
            <div className="space-y-1 max-w-md mx-auto">
              <h2 className="text-lg font-bold text-white">Registration Proof Not Found</h2>
              <p className="text-xs text-slate-400 leading-relaxed">
                We could not find an authoritative registration record matching{' '}
                <span className="font-mono text-rose-400 font-bold">{registrationId}</span>. Please verify the ID format and try again.
              </p>
            </div>
            <div>
              <Link
                to={ROUTES.VERIFICATION.PORTAL}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
              >
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Search Another Registration</span>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Verification Result Dossier */}
      {!isLoading && !error && verificationResult && (
        <VerificationResultCard result={verificationResult} />
      )}
    </div>
  );
};
