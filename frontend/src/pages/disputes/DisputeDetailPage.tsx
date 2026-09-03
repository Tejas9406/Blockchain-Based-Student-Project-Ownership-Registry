import React, { useCallback, useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, RefreshCw, AlertCircle, AlertTriangle } from 'lucide-react';
import { ROUTES } from '../../constants/routes';
import { disputeService } from '../../services/dispute.service';
import { DisputeDetailResponse, NormalizedApiError } from '../../types';
import { normalizeApiError } from '../../utils/error';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { DisputeDetailDossier } from '../../components/disputes/DisputeDetailDossier';

export const DisputeDetailPage: React.FC = () => {
  const { disputeId } = useParams<{ disputeId: string }>();

  const [dispute, setDispute] = useState<DisputeDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<NormalizedApiError | null>(null);

  const fetchDispute = useCallback(async () => {
    if (!disputeId) {
      setError({
        status: 400,
        code: 'VALIDATION_ERROR',
        message: 'No dispute ID provided in URL path.',
      });
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await disputeService.getDispute(disputeId);
      setDispute(data);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [disputeId]);

  useEffect(() => {
    fetchDispute();
  }, [fetchDispute]);

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-4 px-4 sm:px-6">
      {/* Navigation Top Bar */}
      <div className="flex items-center justify-between gap-4">
        <Link
          to={ROUTES.DISPUTES.LIST}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dispute Claims</span>
        </Link>

        <button
          type="button"
          onClick={fetchDispute}
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
          data-testid="dispute-detail-loading"
          className="p-12 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col items-center justify-center text-center space-y-4"
        >
          <LoadingSpinner size="lg" />
          <div className="space-y-1">
            <h2 className="text-base font-bold text-white">Retrieving Dispute Record</h2>
            <p className="text-xs text-slate-400">
              Fetching authoritative claim evidence and on-chain status for{' '}
              <span className="font-mono text-amber-400 font-bold">{disputeId}</span>...
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
              <h2 className="text-lg font-bold text-white">Dispute Record Not Found</h2>
              <p className="text-xs text-slate-400 leading-relaxed">
                We could not find a registered dispute claim matching{' '}
                <span className="font-mono text-rose-400 font-bold">{disputeId}</span>. Please verify the dispute identifier or return to the registry.
              </p>
            </div>
            <div>
              <Link
                to={ROUTES.DISPUTES.LIST}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
              >
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>Return to Disputes List</span>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Dispute Dossier Details */}
      {!isLoading && !error && dispute && (
        <DisputeDetailDossier dispute={dispute} />
      )}
    </div>
  );
};
