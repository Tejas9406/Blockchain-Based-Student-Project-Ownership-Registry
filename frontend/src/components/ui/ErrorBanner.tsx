import React from 'react';
import { AlertCircle, RefreshCw, X } from 'lucide-react';
import { NormalizedApiError } from '../../types';

export interface ErrorBannerProps {
  error: NormalizedApiError | string | null;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  error,
  onRetry,
  onDismiss,
  className = '',
}) => {
  if (!error) return null;

  const message = typeof error === 'string' ? error : error.message;
  const code = typeof error === 'object' && error?.code ? error.code : undefined;

  return (
    <div
      className={`p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-red-200 flex items-start justify-between gap-3 ${className}`}
      role="alert"
    >
      <div className="flex items-start gap-3 flex-1 min-w-0">
        <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
        <div className="min-w-0">
          {code && <div className="text-xs font-mono font-semibold text-red-300 mb-0.5">{code}</div>}
          <div className="text-sm break-words">{message}</div>
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-red-900/60 hover:bg-red-800 text-xs font-semibold text-white transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry</span>
          </button>
        )}
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="p-1 rounded-lg hover:bg-red-900/60 text-red-400 hover:text-red-200 transition-colors"
            title="Dismiss error"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};
