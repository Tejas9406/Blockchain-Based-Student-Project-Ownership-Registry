import React, { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertTriangle, Plus, RefreshCw, Search, ShieldAlert, FolderGit2 } from 'lucide-react';
import { disputeService } from '../../services/dispute.service';
import { projectService } from '../../services/project.service';
import { DisputeDetailResponse, NormalizedApiError } from '../../types';
import { normalizeApiError } from '../../utils/error';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { DisputeCard } from '../../components/disputes/DisputeCard';
import { CreateDisputeModal } from '../../components/disputes/CreateDisputeModal';

export const DisputesPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryProjectId = searchParams.get('projectId') || '';

  const [disputes, setDisputes] = useState<DisputeDetailResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<NormalizedApiError | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchFilter, setSearchFilter] = useState(queryProjectId);

  const fetchDisputes = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (queryProjectId) {
        // Direct project disputes lookup
        const results = await disputeService.listProjectDisputes(queryProjectId);
        setDisputes(results);
      } else {
        // Fetch disputes across user's registered projects
        const userProjects = await projectService.listProjects({ page_size: 50 });
        const allDisputesPromises = userProjects.data.map(async (p) => {
          try {
            return await disputeService.listProjectDisputes(p.public_id);
          } catch {
            return [];
          }
        });

        const nestedDisputes = await Promise.all(allDisputesPromises);
        const flattened = nestedDisputes.flat();

        // De-duplicate by public_id
        const uniqueDisputes = Array.from(
          new Map(flattened.map((d) => [d.public_id, d])).values()
        );

        setDisputes(uniqueDisputes);
      }
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [queryProjectId]);

  useEffect(() => {
    fetchDisputes();
  }, [fetchDisputes]);

  const handleCreateSuccess = (newDispute: DisputeDetailResponse) => {
    setDisputes((prev) => [newDispute, ...prev]);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = searchFilter.trim();
    if (clean) {
      setSearchParams({ projectId: clean });
    } else {
      setSearchParams({});
    }
  };

  const filteredDisputes = disputes.filter((d) => {
    if (!searchFilter.trim() || queryProjectId) return true;
    const term = searchFilter.toLowerCase();
    return (
      d.public_id.toLowerCase().includes(term) ||
      d.project_public_id.toLowerCase().includes(term) ||
      d.project_title.toLowerCase().includes(term) ||
      (d.registration_id && d.registration_id.toLowerCase().includes(term))
    );
  });

  return (
    <div className="space-y-6">
      {/* Top Header & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1">
            <ShieldAlert className="w-4 h-4" />
            <span>MODULE 8: CLAIMS & DISPUTES</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Ownership Claims & Dispute Registry
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Track academic plagiarism claims, review prior art evidence manifests, and view on-chain resolution statuses.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={fetchDisputes}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white bg-slate-900 border border-slate-800 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-xs font-bold text-slate-950 transition-colors shadow-lg shadow-amber-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>File Dispute Claim</span>
          </button>
        </div>
      </div>

      {/* Query scope banner if filtered by specific project */}
      {queryProjectId && (
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
          <div className="flex items-center gap-2 text-slate-300">
            <FolderGit2 className="w-4 h-4 text-emerald-400" />
            <span>Showing dispute claims for project:</span>
            <span className="font-mono font-bold text-white">{queryProjectId}</span>
          </div>
          <button
            type="button"
            onClick={() => {
              setSearchFilter('');
              setSearchParams({});
            }}
            className="text-xs text-amber-400 hover:underline font-semibold"
          >
            View All Disputes
          </button>
        </div>
      )}

      {/* Search Input Filter */}
      {!queryProjectId && (
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Search by Dispute ID (DSP-...), Project ID (PRJ-...), Registration ID, or Title..."
              className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
          >
            Search
          </button>
        </form>
      )}

      {/* Error Banner */}
      {error && (
        <ErrorBanner error={error} onDismiss={() => setError(null)} />
      )}

      {/* Loading State */}
      {isLoading && (
        <div
          data-testid="disputes-loading"
          className="p-12 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col items-center justify-center text-center space-y-3"
        >
          <LoadingSpinner size="lg" />
          <p className="text-xs text-slate-400">Loading authoritative dispute records from registry...</p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && filteredDisputes.length === 0 && (
        <div
          data-testid="disputes-empty"
          className="p-12 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-4"
        >
          <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto text-amber-400">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div className="space-y-1 max-w-sm mx-auto">
            <h3 className="text-base font-bold text-white">No Dispute Claims Logged</h3>
            <p className="text-xs text-slate-400">
              {queryProjectId
                ? `No ownership or plagiarism disputes have been filed against project ${queryProjectId}.`
                : 'There are currently no active or historical ownership dispute records on your registered projects.'}
            </p>
          </div>
          <div>
            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-amber-400 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>File Dispute Claim</span>
            </button>
          </div>
        </div>
      )}

      {/* Dispute List Cards */}
      {!isLoading && !error && filteredDisputes.length > 0 && (
        <div className="grid grid-cols-1 gap-4">
          {filteredDisputes.map((dispute) => (
            <DisputeCard key={dispute.public_id} dispute={dispute} />
          ))}
        </div>
      )}

      {/* Create Dispute Modal */}
      <CreateDisputeModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleCreateSuccess}
        initialProjectId={queryProjectId}
      />
    </div>
  );
};
