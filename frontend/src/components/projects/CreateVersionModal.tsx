import React, { useState } from 'react';
import {
  X,
  Layers,
  Plus,
  Trash2,
  FileCode,
  FileText,
  FileCheck,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { projectService } from '../../services/project.service';
import {
  LifecycleStage,
  NormalizedApiError,
  ProjectVersionDetail,
  ArtifactResponse,
} from '../../types';
import { normalizeApiError } from '../../utils/error';
import { ErrorBanner } from '../ui/ErrorBanner';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export interface CreateVersionModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (version: ProjectVersionDetail) => void;
  availableArtifacts?: ArtifactResponse[];
}

const LIFECYCLE_OPTIONS: { stage: LifecycleStage; label: string; desc: string }[] = [
  { stage: 'IDEA', label: 'Idea Stage', desc: 'Concept, problem definition, feasibility notes' },
  { stage: 'DESIGN', label: 'Design Stage', desc: 'Architecture, diagrams, API contracts, threat model' },
  { stage: 'PROTOTYPE', label: 'Prototype Stage', desc: 'Working implementation, demo build, MVP code' },
  { stage: 'FINAL', label: 'Final Stage', desc: 'Production release, defense presentation, final thesis' },
];

export const CreateVersionModal: React.FC<CreateVersionModalProps> = ({
  projectId,
  isOpen,
  onClose,
  onSuccess,
  availableArtifacts = [],
}) => {
  const [versionTag, setVersionTag] = useState('');
  const [lifecycleStage, setLifecycleStage] = useState<LifecycleStage>('IDEA');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedArtifactIds, setSelectedArtifactIds] = useState<string[]>([]);
  const [manualArtifactInput, setManualArtifactInput] = useState('');

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<NormalizedApiError | null>(null);

  if (!isOpen) return null;

  const handleToggleArtifact = (artifactId: string) => {
    setSelectedArtifactIds((prev) =>
      prev.includes(artifactId)
        ? prev.filter((id) => id !== artifactId)
        : [...prev, artifactId]
    );
  };

  const handleAddManualArtifact = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = manualArtifactInput.trim();
    if (!trimmed) return;
    if (!selectedArtifactIds.includes(trimmed)) {
      setSelectedArtifactIds((prev) => [...prev, trimmed]);
    }
    setManualArtifactInput('');
  };

  const handleRemoveArtifactId = (idToRemove: string) => {
    setSelectedArtifactIds((prev) => prev.filter((id) => id !== idToRemove));
  };

  const validate = (): boolean => {
    const errors: Record<string, string> = {};

    if (!versionTag.trim()) {
      errors.versionTag = 'Version tag is required (e.g. v1.0).';
    } else if (versionTag.trim().length > 50) {
      errors.versionTag = 'Version tag must be 50 characters or fewer.';
    }

    if (!title.trim()) {
      errors.title = 'Milestone title is required.';
    } else if (title.trim().length > 255) {
      errors.title = 'Milestone title must be 255 characters or fewer.';
    }

    if (!lifecycleStage) {
      errors.lifecycleStage = 'Please select a lifecycle stage.';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const generateIdempotencyKey = (): string => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return `idemp-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    setApiError(null);
    if (!validate()) return;

    setIsSubmitting(true);

    try {
      const idempotencyKey = generateIdempotencyKey();
      const payload = {
        version_tag: versionTag.trim(),
        lifecycle_stage: lifecycleStage,
        title: title.trim(),
        description: description.trim() ? description.trim() : undefined,
        artifact_ids: selectedArtifactIds,
      };

      const createdVersion = await projectService.createVersion(
        projectId,
        payload,
        idempotencyKey
      );

      onSuccess(createdVersion);
      onClose();
    } catch (err) {
      setApiError(normalizeApiError(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatBytes = (bytes?: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-version-title"
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-8">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h2 id="create-version-title" className="text-lg font-bold text-white">
                Create Milestone Version Snapshot
              </h2>
              <p className="text-xs text-slate-400">
                Record an immutable project milestone and queue for on-chain anchoring.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close modal"
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body / Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {apiError && <ErrorBanner error={apiError} />}

          {/* Form Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Version Tag */}
            <div className="space-y-1.5">
              <label htmlFor="version-tag" className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Version Tag <span className="text-rose-400">*</span>
              </label>
              <input
                id="version-tag"
                type="text"
                value={versionTag}
                onChange={(e) => {
                  setVersionTag(e.target.value);
                  if (validationErrors.versionTag) {
                    setValidationErrors((prev) => ({ ...prev, versionTag: '' }));
                  }
                }}
                disabled={isSubmitting}
                placeholder="e.g. v1.0, v0.2.1"
                className={`w-full px-3.5 py-2.5 rounded-xl bg-slate-950/70 border ${
                  validationErrors.versionTag ? 'border-rose-500/60 focus:border-rose-400' : 'border-slate-800 focus:border-emerald-500'
                } text-white text-sm placeholder-slate-500 font-mono focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-colors`}
              />
              {validationErrors.versionTag && (
                <p className="text-[11px] text-rose-400 flex items-center gap-1 mt-1">
                  <AlertCircle className="w-3 h-3" />
                  <span>{validationErrors.versionTag}</span>
                </p>
              )}
            </div>

            {/* Title */}
            <div className="space-y-1.5">
              <label htmlFor="version-title" className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Milestone Title <span className="text-rose-400">*</span>
              </label>
              <input
                id="version-title"
                type="text"
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  if (validationErrors.title) {
                    setValidationErrors((prev) => ({ ...prev, title: '' }));
                  }
                }}
                disabled={isSubmitting}
                placeholder="e.g. System Architecture & Threat Model"
                className={`w-full px-3.5 py-2.5 rounded-xl bg-slate-950/70 border ${
                  validationErrors.title ? 'border-rose-500/60 focus:border-rose-400' : 'border-slate-800 focus:border-emerald-500'
                } text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-colors`}
              />
              {validationErrors.title && (
                <p className="text-[11px] text-rose-400 flex items-center gap-1 mt-1">
                  <AlertCircle className="w-3 h-3" />
                  <span>{validationErrors.title}</span>
                </p>
              )}
            </div>
          </div>

          {/* Lifecycle Stage Selection */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
              Lifecycle Stage <span className="text-rose-400">*</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {LIFECYCLE_OPTIONS.map((opt) => {
                const isSelected = lifecycleStage === opt.stage;
                return (
                  <button
                    key={opt.stage}
                    type="button"
                    onClick={() => setLifecycleStage(opt.stage)}
                    disabled={isSubmitting}
                    className={`p-3 rounded-xl text-left border transition-all flex items-start justify-between gap-2 ${
                      isSelected
                        ? 'bg-emerald-500/10 border-emerald-500/50 text-white shadow-sm'
                        : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    <div className="space-y-0.5 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-mono font-bold tracking-wider">{opt.stage}</span>
                        <span className="text-[11px] text-slate-300">({opt.label})</span>
                      </div>
                      <p className="text-[11px] text-slate-500 truncate">{opt.desc}</p>
                    </div>
                    {isSelected && (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    )}
                  </button>
                );
              })}
            </div>
            {validationErrors.lifecycleStage && (
              <p className="text-[11px] text-rose-400 flex items-center gap-1 mt-1">
                <AlertCircle className="w-3 h-3" />
                <span>{validationErrors.lifecycleStage}</span>
              </p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <label htmlFor="version-description" className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
              Description / Milestone Notes <span className="text-slate-500 font-normal">(Optional)</span>
            </label>
            <textarea
              id="version-description"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={isSubmitting}
              placeholder="Detailed changelog, architectural notes, or milestone deliverable descriptions..."
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-colors"
            />
          </div>

          {/* Artifact Selection Section */}
          <div className="space-y-3 border-t border-slate-800 pt-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Attach Project Artifacts
                </label>
                <p className="text-[11px] text-slate-400">
                  Select existing files uploaded for this project to combine into the version root.
                </p>
              </div>
              <span className="text-xs font-mono font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                {selectedArtifactIds.length} Selected
              </span>
            </div>

            {/* Available Project Artifacts Checklist */}
            {availableArtifacts.length > 0 ? (
              <div className="max-h-48 overflow-y-auto space-y-1.5 p-2 rounded-xl bg-slate-950/50 border border-slate-800/80">
                {availableArtifacts.map((art) => {
                  const isChecked = selectedArtifactIds.includes(art.public_id);
                  return (
                    <label
                      key={art.public_id}
                      className={`flex items-center justify-between gap-3 p-2.5 rounded-lg border cursor-pointer transition-colors ${
                        isChecked
                          ? 'bg-emerald-500/10 border-emerald-500/30 text-white'
                          : 'bg-slate-900/40 border-slate-800 text-slate-300 hover:bg-slate-900'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleToggleArtifact(art.public_id)}
                          disabled={isSubmitting}
                          className="rounded border-slate-700 bg-slate-950 text-emerald-500 focus:ring-emerald-500"
                        />
                        <div className="w-6 h-6 rounded bg-slate-800 flex items-center justify-center text-slate-400 shrink-0">
                          {art.artifact_category === 'SOURCE_CODE' ? (
                            <FileCode className="w-3.5 h-3.5 text-blue-400" />
                          ) : art.artifact_category === 'DOCUMENTATION' ? (
                            <FileText className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <FileCheck className="w-3.5 h-3.5 text-amber-400" />
                          )}
                        </div>
                        <div className="min-w-0">
                          <p className="text-xs font-semibold truncate max-w-xs">{art.file_name}</p>
                          <p className="text-[10px] font-mono text-slate-500">
                            {art.public_id} • {formatBytes(art.file_size_bytes)}
                          </p>
                        </div>
                      </div>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700 shrink-0">
                        {art.artifact_category}
                      </span>
                    </label>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic p-3 rounded-lg bg-slate-950/30 text-center border border-slate-800/60">
                No pre-loaded artifacts found for this project. You may enter artifact IDs manually below or upload files via the Artifacts page.
              </p>
            )}

            {/* Manual Artifact ID Entry */}
            <div className="pt-2">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={manualArtifactInput}
                  onChange={(e) => setManualArtifactInput(e.target.value)}
                  disabled={isSubmitting}
                  placeholder="Enter artifact ID (e.g. ART-202608-11E54)"
                  className="flex-1 px-3 py-1.5 rounded-xl bg-slate-950/70 border border-slate-800 text-white text-xs font-mono placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
                <button
                  type="button"
                  onClick={handleAddManualArtifact}
                  disabled={isSubmitting || !manualArtifactInput.trim()}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-xs font-semibold text-white transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add ID</span>
                </button>
              </div>

              {/* Selected manual tags list */}
              {selectedArtifactIds.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {selectedArtifactIds.map((id) => (
                    <span
                      key={id}
                      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-slate-800 border border-slate-700 text-xs font-mono text-emerald-400"
                    >
                      <span>{id}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveArtifactId(id)}
                        disabled={isSubmitting}
                        aria-label={`Remove artifact ${id}`}
                        className="text-slate-500 hover:text-rose-400 transition-colors"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Modal Footer Controls */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:bg-emerald-600/50 text-xs font-bold text-slate-950 transition-colors shadow-lg shadow-emerald-500/20"
            >
              {isSubmitting ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span>Anchoring Milestone Snapshot...</span>
                </>
              ) : (
                <>
                  <Layers className="w-4 h-4" />
                  <span>Create & Anchor Milestone</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
