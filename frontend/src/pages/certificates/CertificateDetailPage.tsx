import React, { useCallback, useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, RefreshCw, AlertCircle, ShieldCheck, ShieldAlert } from 'lucide-react';
import { ROUTES } from '../../constants/routes';
import { certificateService } from '../../services/certificate.service';
import { CertificateMetadataData, NormalizedApiError } from '../../types';
import { normalizeApiError } from '../../utils/error';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { CertificatePreviewCard } from '../../components/certificates/CertificatePreviewCard';

export const CertificateDetailPage: React.FC = () => {
  const { registrationId } = useParams<{ registrationId: string }>();

  const [certificate, setCertificate] = useState<CertificateMetadataData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<NormalizedApiError | null>(null);

  const fetchCertificate = useCallback(async () => {
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
      const data = await certificateService.getCertificateMetadata(registrationId);
      setCertificate(data);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [registrationId]);

  useEffect(() => {
    fetchCertificate();
  }, [fetchCertificate]);

  return (
    <div className="max-w-5xl mx-auto space-y-6 py-4 px-4 sm:px-6">
      {/* Top Navigation Bar */}
      <div className="flex items-center justify-between gap-4">
        <Link
          to={ROUTES.VERIFICATION.PORTAL}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Verification Portal</span>
        </Link>

        <button
          type="button"
          onClick={fetchCertificate}
          disabled={isLoading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white bg-slate-900 border border-slate-800 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div
          data-testid="certificate-loading"
          className="p-12 rounded-3xl bg-slate-900/60 border border-slate-800 flex flex-col items-center justify-center text-center space-y-4"
        >
          <LoadingSpinner size="lg" />
          <div className="space-y-1">
            <h2 className="text-base font-bold text-white">Retrieving Ownership Certificate</h2>
            <p className="text-xs text-slate-400">
              Validating blockchain anchoring and cryptographic provenance for{' '}
              <span className="font-mono text-amber-400 font-bold">{registrationId}</span>...
            </p>
          </div>
        </div>
      )}

      {/* Error / Not Found / Disputed State */}
      {!isLoading && error && (
        <div className="space-y-6">
          <ErrorBanner error={error} onDismiss={() => setError(null)} />

          <div className="p-8 rounded-3xl bg-slate-900/60 border border-rose-900/30 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto text-rose-400">
              {error.status === 409 ? <ShieldAlert className="w-6 h-6 text-amber-400" /> : <AlertCircle className="w-6 h-6" />}
            </div>
            <div className="space-y-1 max-w-md mx-auto">
              <h2 className="text-lg font-bold text-white">
                {error.status === 409 ? 'Certificate Unavailable Due to Dispute' : 'Certificate Not Found'}
              </h2>
              <p className="text-xs text-slate-400 leading-relaxed">
                {error.status === 409
                  ? 'An ownership or plagiarism claim has been upheld or is under review for this project version. Certificate generation is locked.'
                  : `We could not find an anchored certificate matching registration ID "${registrationId}".`}
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Link
                to={ROUTES.VERIFICATION.PORTAL}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
              >
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Search Verification Portal</span>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Certificate Preview Card */}
      {!isLoading && !error && certificate && (
        <CertificatePreviewCard certificate={certificate} />
      )}
    </div>
  );
};
