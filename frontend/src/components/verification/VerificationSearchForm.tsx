import React, { useState } from 'react';
import { ShieldCheck, Hash, Upload, Search, FileText, X } from 'lucide-react';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export type VerificationTabType = 'registration_id' | 'sha256_hash' | 'file_upload';

export interface VerificationSearchFormProps {
  isLoading: boolean;
  onVerifyRegistrationId: (registrationId: string) => void;
  onVerifyHash: (hash: string, registrationId?: string) => void;
  onVerifyFile: (file: File, registrationId?: string) => void;
  initialRegistrationId?: string;
}

export const VerificationSearchForm: React.FC<VerificationSearchFormProps> = ({
  isLoading,
  onVerifyRegistrationId,
  onVerifyHash,
  onVerifyFile,
  initialRegistrationId = '',
}) => {
  const [activeTab, setActiveTab] = useState<VerificationTabType>('registration_id');

  // Form states
  const [registrationId, setRegistrationId] = useState(initialRegistrationId);
  const [sha256Hash, setSha256Hash] = useState('');
  const [scopedRegId, setScopedRegId] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (activeTab === 'registration_id') {
      const trimmed = registrationId.trim();
      if (!trimmed) {
        setValidationError('Please enter a Registration ID (e.g. REG-2026-A8F92D).');
        return;
      }
      onVerifyRegistrationId(trimmed);
    } else if (activeTab === 'sha256_hash') {
      const trimmedHash = sha256Hash.trim().toLowerCase();
      if (!trimmedHash) {
        setValidationError('Please enter a 64-character SHA-256 hexadecimal hash.');
        return;
      }
      if (!/^[0-9a-f]{64}$/.test(trimmedHash)) {
        setValidationError('SHA-256 hash must be exactly 64 hexadecimal characters.');
        return;
      }
      onVerifyHash(trimmedHash, scopedRegId.trim() || undefined);
    } else if (activeTab === 'file_upload') {
      if (!selectedFile) {
        setValidationError('Please select or drop a file to verify.');
        return;
      }
      if (selectedFile.size > 50 * 1024 * 1024) {
        setValidationError('File size exceeds the 50 MB limit.');
        return;
      }
      onVerifyFile(selectedFile, scopedRegId.trim() || undefined);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
      setValidationError(null);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setValidationError(null);
    }
  };

  return (
    <div className="p-6 sm:p-8 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-6">
      {/* Search Mode Tabs */}
      <div className="flex border-b border-slate-800 gap-2 pb-2" role="tablist" aria-label="Verification Methods">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'registration_id'}
          onClick={() => {
            setActiveTab('registration_id');
            setValidationError(null);
          }}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
            activeTab === 'registration_id'
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Registration ID</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'sha256_hash'}
          onClick={() => {
            setActiveTab('sha256_hash');
            setValidationError(null);
          }}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
            activeTab === 'sha256_hash'
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <Hash className="w-4 h-4" />
          <span>SHA-256 Digest</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'file_upload'}
          onClick={() => {
            setActiveTab('file_upload');
            setValidationError(null);
          }}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
            activeTab === 'file_upload'
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <Upload className="w-4 h-4" />
          <span>Direct File Verify</span>
        </button>
      </div>

      {/* Verification Search Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {activeTab === 'registration_id' && (
          <div className="space-y-2">
            <label htmlFor="registration-id-input" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Unique Project Certificate Registration ID
            </label>
            <div className="relative">
              <input
                id="registration-id-input"
                type="text"
                value={registrationId}
                onChange={(e) => setRegistrationId(e.target.value)}
                placeholder="e.g. REG-2026-A8F92D"
                disabled={isLoading}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white font-mono placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 disabled:opacity-50"
              />
            </div>
            <p className="text-[11px] text-slate-500">
              Format: <span className="font-mono text-slate-400">REG-YYYY-XXXXX</span> found on ownership certificates and milestone receipts.
            </p>
          </div>
        )}

        {activeTab === 'sha256_hash' && (
          <div className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="sha256-hash-input" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                Raw 64-Character SHA-256 Digest
              </label>
              <input
                id="sha256-hash-input"
                type="text"
                value={sha256Hash}
                onChange={(e) => setSha256Hash(e.target.value)}
                placeholder="e.g. 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
                disabled={isLoading}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white font-mono placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 disabled:opacity-50"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="scoped-reg-id-hash" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                Optional: Scope to Specific Registration ID
              </label>
              <input
                id="scoped-reg-id-hash"
                type="text"
                value={scopedRegId}
                onChange={(e) => setScopedRegId(e.target.value)}
                placeholder="Optional (e.g. REG-2026-A8F92D)"
                disabled={isLoading}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 text-xs text-white font-mono placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 disabled:opacity-50"
              />
            </div>
          </div>
        )}

        {activeTab === 'file_upload' && (
          <div className="space-y-4">
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors ${
                dragActive
                  ? 'border-emerald-500 bg-emerald-500/10'
                  : 'border-slate-700 bg-slate-950/50 hover:border-slate-600'
              }`}
            >
              {selectedFile ? (
                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900 border border-slate-800 text-left">
                  <div className="flex items-center gap-3 overflow-hidden">
                    <FileText className="w-6 h-6 text-emerald-400 shrink-0" />
                    <div className="overflow-hidden">
                      <p className="text-sm font-semibold text-white truncate">{selectedFile.name}</p>
                      <p className="text-xs text-slate-400">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedFile(null)}
                    aria-label="Remove selected file"
                    className="p-1 text-slate-400 hover:text-rose-400"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <Upload className="w-8 h-8 text-slate-400 mx-auto" />
                  <div className="space-y-1">
                    <p className="text-sm text-slate-300">
                      Drag and drop your academic artifact or{' '}
                      <label htmlFor="file-verify-input" className="text-emerald-400 hover:underline cursor-pointer font-semibold">
                        browse files
                      </label>
                    </p>
                    <p className="text-xs text-slate-500">
                      The file is streamed to compute SHA-256 for provenance matching and is immediately discarded. Max 50 MB.
                    </p>
                  </div>
                  <input
                    id="file-verify-input"
                    type="file"
                    onChange={handleFileChange}
                    disabled={isLoading}
                    className="hidden"
                  />
                </div>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="scoped-reg-id-file" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                Optional: Scope to Specific Registration ID
              </label>
              <input
                id="scoped-reg-id-file"
                type="text"
                value={scopedRegId}
                onChange={(e) => setScopedRegId(e.target.value)}
                placeholder="Optional (e.g. REG-2026-A8F92D)"
                disabled={isLoading}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 text-xs text-white font-mono placeholder:text-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 disabled:opacity-50"
              />
            </div>
          </div>
        )}

        {/* Validation Error */}
        {validationError && (
          <p className="text-xs font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3 py-2 rounded-lg">
            {validationError}
          </p>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 disabled:text-slate-600 font-bold text-sm text-slate-950 transition-colors shadow-lg shadow-emerald-500/20 disabled:shadow-none"
        >
          {isLoading ? (
            <>
              <LoadingSpinner size="sm" className="border-slate-950 border-t-transparent" />
              <span>Verifying Provenance Against Blockchain...</span>
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              <span>Verify Ownership Proof</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};
