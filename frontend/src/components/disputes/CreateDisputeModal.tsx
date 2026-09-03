import React, { useState } from 'react';
import { X, AlertTriangle, ShieldCheck, FolderGit2, FileText, HardDrive } from 'lucide-react';
import { disputeService } from '../../services/dispute.service';
import { DisputeCreateRequest, DisputeDetailResponse, DisputeType, NormalizedApiError } from '../../types';
import { normalizeApiError } from '../../utils/error';
import { ErrorBanner } from '../ui/ErrorBanner';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export interface CreateDisputeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (dispute: DisputeDetailResponse) => void;
  initialProjectId?: string;
  initialRegistrationId?: string;
}

const DISPUTE_TYPES: { value: DisputeType; label: string; description: string }[] = [
  {
    value: 'PLAGIARISM',
    label: 'Academic Plagiarism',
    description: 'Code, documentation, or architecture copied without attribution.',
  },
  {
    value: 'UNAUTHORIZED_USE',
    label: 'Unauthorized Use',
    description: 'Proprietary assets, designs, or datasets used without consent.',
  },
  {
    value: 'CITATION_FAILURE',
    label: 'Citation Failure',
    description: 'Failure to cite prior foundational student research.',
  },
  {
    value: 'OTHER',
    label: 'Other Ownership Violation',
    description: 'Other intellectual property or contributor disputes.',
  },
];

export const CreateDisputeModal: React.FC<CreateDisputeModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialProjectId = '',
  initialRegistrationId = '',
}) => {
  const [projectId, setProjectId] = useState(initialProjectId);
  const [registrationId, setRegistrationId] = useState(initialRegistrationId);
  const [disputeType, setDisputeType] = useState<DisputeType>('PLAGIARISM');
  const [claimDescription, setClaimDescription] = useState('');
  const [evidenceUrl, setEvidenceUrl] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<NormalizedApiError | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setError(null);

    const cleanProjId = projectId.trim();
    const cleanRegId = registrationId.trim();
    const cleanDesc = claimDescription.trim();
    const cleanEvidence = evidenceUrl.trim();

    if (!cleanProjId && !cleanRegId) {
      setValidationError('Please specify either a Target Project ID or Certificate Registration ID.');
      return;
    }

    if (cleanDesc.length < 10) {
      setValidationError('Claim description must contain at least 10 non-whitespace characters.');
      return;
    }

    setIsLoading(true);

    try {
      const payload: DisputeCreateRequest = {
        project_id: cleanProjId || undefined,
        registration_id: cleanRegId || undefined,
        dispute_type: disputeType,
        claim_description: cleanDesc,
        evidence_url: cleanEvidence || undefined,
      };

      const result = await disputeService.raiseDispute(payload);
      onSuccess(result);
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
      aria-labelledby="create-dispute-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto"
    >
      <div className="relative w-full max-w-xl my-8 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h2 id="create-dispute-modal-title" className="text-lg font-bold text-white tracking-tight">
                File Ownership Dispute Claim
              </h2>
              <p className="text-xs text-slate-400">
                Submit an immutable prior art or plagiarism assertion against an anchored project version.
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

        {/* Error Banner */}
        {error && (
          <div className="p-6 pb-0">
            <ErrorBanner error={error} onDismiss={() => setError(null)} />
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Target Identifier inputs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label htmlFor="dispute-project-id" className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <FolderGit2 className="w-3.5 h-3.5 text-slate-500" />
                <span>Target Project ID</span>
              </label>
              <input
                id="dispute-project-id"
                type="text"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                placeholder="e.g. PRJ-202609-A8F92"
                disabled={isLoading}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs font-mono text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 disabled:opacity-50"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="dispute-reg-id" className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <ShieldCheck className="w-3.5 h-3.5 text-slate-500" />
                <span>Or Registration ID</span>
              </label>
              <input
                id="dispute-reg-id"
                type="text"
                value={registrationId}
                onChange={(e) => setRegistrationId(e.target.value)}
                placeholder="e.g. REG-2026-A8F92"
                disabled={isLoading}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs font-mono text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 disabled:opacity-50"
              />
            </div>
          </div>

          {/* Dispute Classification */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Dispute Category
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {DISPUTE_TYPES.map((dt) => (
                <button
                  key={dt.value}
                  type="button"
                  onClick={() => setDisputeType(dt.value)}
                  disabled={isLoading}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    disputeType === dt.value
                      ? 'bg-amber-500/10 border-amber-500/40 text-white shadow-sm'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <p className="font-semibold text-xs text-white">{dt.label}</p>
                  <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">{dt.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Factual Description */}
          <div className="space-y-1.5">
            <label htmlFor="dispute-claim-desc" className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
              <FileText className="w-3.5 h-3.5 text-slate-500" />
              <span>Factual Claim & Prior Art Details (Required)</span>
            </label>
            <textarea
              id="dispute-claim-desc"
              rows={4}
              value={claimDescription}
              onChange={(e) => setClaimDescription(e.target.value)}
              placeholder="Explain why this project infringes on prior art, including specific repository links, paper titles, publication timestamps, or shared source code references..."
              disabled={isLoading}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 disabled:opacity-50 resize-none"
            />
            <p className="text-[11px] text-slate-500">
              Minimum 10 characters. Claims are recorded permanently in the audit trail.
            </p>
          </div>

          {/* Evidence URL or CID */}
          <div className="space-y-1.5">
            <label htmlFor="dispute-evidence-url" className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
              <HardDrive className="w-3.5 h-3.5 text-slate-500" />
              <span>Prior Art Evidence (Optional IPFS CID or Public URL)</span>
            </label>
            <input
              id="dispute-evidence-url"
              type="text"
              value={evidenceUrl}
              onChange={(e) => setEvidenceUrl(e.target.value)}
              placeholder="e.g. bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m"
              disabled={isLoading}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs font-mono text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 disabled:opacity-50"
            />
          </div>

          {/* Validation Error */}
          {validationError && (
            <p className="text-xs font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-2 rounded-lg">
              {validationError}
            </p>
          )}

          {/* Actions */}
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
              className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:bg-slate-800 disabled:text-slate-600 text-xs font-bold text-slate-950 transition-colors shadow-lg shadow-amber-500/20 disabled:shadow-none"
            >
              {isLoading ? (
                <>
                  <LoadingSpinner size="sm" className="border-slate-950 border-t-transparent" />
                  <span>Submitting Dispute to Relayer...</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4" />
                  <span>Submit Claim</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
