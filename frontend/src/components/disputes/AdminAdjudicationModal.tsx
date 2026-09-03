import React, { useState } from 'react';
import {
  X,
  Gavel,
  CheckCircle2,
  XCircle,
  FileText,
  AlertTriangle,
} from 'lucide-react';
import { disputeService } from '../../services/dispute.service';
import {
  DisputeDetailResponse,
  DisputeAdjudicateRequest,
  NormalizedApiError,
} from '../../types';
import { normalizeApiError } from '../../utils/error';
import { ErrorBanner } from '../ui/ErrorBanner';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export interface AdminAdjudicationModalProps {
  dispute: DisputeDetailResponse;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (updatedDispute: DisputeDetailResponse) => void;
}

export const AdminAdjudicationModal: React.FC<AdminAdjudicationModalProps> = ({
  dispute,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [resolutionStatus, setResolutionStatus] = useState<'RESOLVED' | 'REJECTED'>('REJECTED');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [isConfirmed, setIsConfirmed] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<NormalizedApiError | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setError(null);

    const cleanNotes = resolutionNotes.trim();
    if (cleanNotes.length < 5) {
      setValidationError('Resolution rationale notes must be at least 5 characters long.');
      return;
    }

    if (cleanNotes.length > 2000) {
      setValidationError('Resolution rationale notes cannot exceed 2000 characters.');
      return;
    }

    if (!isConfirmed) {
      setValidationError('Please confirm that you have reviewed the evidence and authorize this on-chain adjudication.');
      return;
    }

    setIsLoading(true);

    try {
      const payload: DisputeAdjudicateRequest = {
        resolution_status: resolutionStatus,
        resolution_notes: cleanNotes,
      };

      const updated = await disputeService.adjudicateDispute(dispute.public_id, payload);
      onSuccess(updated);
      onClose();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="adjudication-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-sm overflow-y-auto"
    >
      <div className="relative w-full max-w-xl my-8 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Gavel className="w-5 h-5" />
            </div>
            <div>
              <h2 id="adjudication-modal-title" className="text-lg font-bold text-white tracking-tight">
                Adjudicate Dispute Claim
              </h2>
              <p className="text-xs text-slate-400">
                Official institutional review and on-chain dispute resolution.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            aria-label="Close dialog"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Dispute Context Banner */}
        <div className="px-6 py-3 bg-slate-950/70 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-mono text-amber-400 font-bold">{dispute.public_id}</span>
            <span className="text-slate-500">•</span>
            <span className="text-slate-300 truncate max-w-xs">{dispute.project_title}</span>
          </div>
          {dispute.registration_id && (
            <span className="font-mono text-[11px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              {dispute.registration_id}
            </span>
          )}
        </div>

        {/* Error Banner */}
        {error && (
          <div className="p-6 pb-0">
            <ErrorBanner error={error} onDismiss={() => setError(null)} />
          </div>
        )}

        {/* Adjudication Form */}
        <form noValidate onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Outcome Decision Selector */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Administrative Decision Outcome
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* REJECTED Card */}
              <button
                type="button"
                onClick={() => setResolutionStatus('REJECTED')}
                disabled={isLoading}
                className={`p-4 rounded-xl border text-left transition-all ${
                  resolutionStatus === 'REJECTED'
                    ? 'bg-emerald-500/10 border-emerald-500/50 text-white shadow-sm ring-1 ring-emerald-500/30'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-2">
                  <CheckCircle2
                    className={`w-4 h-4 ${
                      resolutionStatus === 'REJECTED' ? 'text-emerald-400' : 'text-slate-500'
                    }`}
                  />
                  <span className="font-bold text-xs text-white">REJECTED (Claim Dismissed)</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">
                  Claimant failed to prove prior art or infringement. Project ownership standing is verified and cleared.
                </p>
              </button>

              {/* RESOLVED Card */}
              <button
                type="button"
                onClick={() => setResolutionStatus('RESOLVED')}
                disabled={isLoading}
                className={`p-4 rounded-xl border text-left transition-all ${
                  resolutionStatus === 'RESOLVED'
                    ? 'bg-rose-500/10 border-rose-500/50 text-white shadow-sm ring-1 ring-rose-500/30'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-2">
                  <XCircle
                    className={`w-4 h-4 ${
                      resolutionStatus === 'RESOLVED' ? 'text-rose-400' : 'text-slate-500'
                    }`}
                  />
                  <span className="font-bold text-xs text-white">RESOLVED (Claim Upheld)</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">
                  Evidence confirms plagiarism or unauthorized use. The project version is marked as disputed on-chain.
                </p>
              </button>
            </div>
          </div>

          {/* Resolution Notes / Rationale */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <label
                htmlFor="adjudication-notes"
                className="flex items-center gap-1.5 font-semibold uppercase tracking-wider text-slate-400"
              >
                <FileText className="w-3.5 h-3.5 text-slate-500" />
                <span>Adjudication Rationale & Findings (Required)</span>
              </label>
              <span className="text-[11px] font-mono text-slate-500">
                {resolutionNotes.trim().length} / 2000
              </span>
            </div>
            <textarea
              id="adjudication-notes"
              rows={4}
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="Detail the factual findings, comparison with prior art evidence CIDs, committee evaluation, and justification for this outcome..."
              disabled={isLoading}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3.5 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 disabled:opacity-50 resize-y"
            />
          </div>

          {/* Legal / Smart Contract Notice */}
          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-start gap-2.5 text-xs text-amber-300">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              <strong className="text-amber-200">Official Decision:</strong> Submitting this adjudication will broadcast a <code className="font-mono text-amber-300">resolveDispute</code> transaction to the smart contract via the relayer. The outcome and rationale will be permanently recorded.
            </p>
          </div>

          {/* Checkbox Confirmation */}
          <div className="flex items-start gap-2.5 pt-1">
            <input
              id="adjudication-confirm"
              type="checkbox"
              checked={isConfirmed}
              onChange={(e) => setIsConfirmed(e.target.checked)}
              disabled={isLoading}
              className="mt-0.5 rounded border-slate-700 bg-slate-950 text-amber-500 focus:ring-amber-500 focus:ring-offset-slate-900"
            />
            <label htmlFor="adjudication-confirm" className="text-xs text-slate-300 cursor-pointer leading-snug select-none">
              I certify as an authorized institutional administrator that this dispute has been thoroughly evaluated against verified repository evidence.
            </label>
          </div>

          {/* Validation Error */}
          {validationError && (
            <p className="text-xs font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-2 rounded-lg">
              {validationError}
            </p>
          )}

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={isLoading}
              className={`inline-flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-bold transition-all shadow-lg disabled:shadow-none disabled:opacity-50 ${
                resolutionStatus === 'RESOLVED'
                  ? 'bg-rose-500 hover:bg-rose-400 text-white shadow-rose-500/20'
                  : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-emerald-500/20'
              }`}
            >
              {isLoading ? (
                <>
                  <LoadingSpinner size="sm" className="border-current border-t-transparent" />
                  <span>Broadcasting Resolution...</span>
                </>
              ) : (
                <>
                  <Gavel className="w-4 h-4" />
                  <span>Submit Final Adjudication</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
