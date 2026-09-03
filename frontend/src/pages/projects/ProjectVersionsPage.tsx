import React, { useCallback, useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Layers,
  ArrowLeft,
  Plus,
  RefreshCw,
  FolderGit2,
  FileUp,
  ShieldCheck,
  CheckCircle,
} from 'lucide-react';
import { projectService } from '../../services/project.service';
import {
  ProjectSummary,
  ProjectVersionDetail,
  ArtifactResponse,
  NormalizedApiError,
} from '../../types';
import { normalizeApiError } from '../../utils/error';
import { ROUTES } from '../../constants/routes';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import {
  ProjectVersionCard,
  CreateVersionModal,
  LifecycleBadge,
  StatusBadge,
} from '../../components/projects';

export const ProjectVersionsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();

  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [versions, setVersions] = useState<ProjectVersionDetail[]>([]);
  const [availableArtifacts, setAvailableArtifacts] = useState<ArtifactResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<NormalizedApiError | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchVersionsData = useCallback(async () => {
    if (!projectId) {
      setError({
        status: 400,
        code: 'INVALID_PROJECT_ID',
        message: 'No project identifier specified.',
      });
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const [projectData, versionsData] = await Promise.all([
        projectService.getProject(projectId),
        projectService.listVersions(projectId),
      ]);

      setProject(projectData);

      // Sort versions in strictly ascending version_index order
      const sortedVersions = [...versionsData].sort(
        (a, b) => a.version_index - b.version_index
      );
      setVersions(sortedVersions);

      // Collect all artifacts present in versions for artifact selection
      const extractedArtifacts: ArtifactResponse[] = [];
      const seenIds = new Set<string>();

      sortedVersions.forEach((v) => {
        if (Array.isArray(v.artifacts)) {
          v.artifacts.forEach((art) => {
            if (!seenIds.has(art.public_id)) {
              seenIds.add(art.public_id);
              extractedArtifacts.push(art);
            }
          });
        }
      });

      setAvailableArtifacts(extractedArtifacts);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchVersionsData();
  }, [fetchVersionsData]);

  const handleCreateSuccess = (newVersion: ProjectVersionDetail) => {
    setVersions((prev) => {
      const updated = [...prev.filter((v) => v.public_id !== newVersion.public_id), newVersion];
      return updated.sort((a, b) => a.version_index - b.version_index);
    });

    if (newVersion.artifacts && newVersion.artifacts.length > 0) {
      setAvailableArtifacts((prev) => {
        const existingIds = new Set(prev.map((a) => a.public_id));
        const newOnes = (newVersion.artifacts || []).filter(
          (a) => !existingIds.has(a.public_id)
        );
        return [...prev, ...newOnes];
      });
    }

    setSuccessMessage(`Milestone version ${newVersion.version_tag} (#${newVersion.version_index}) created and queued for anchoring.`);
    setTimeout(() => setSuccessMessage(null), 5000);
  };

  if (isLoading && !project) {
    return (
      <div className="max-w-5xl mx-auto py-24 px-4 flex justify-center">
        <LoadingSpinner size="lg" message="Loading project milestones and versions..." />
      </div>
    );
  }

  if (error && !project) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 space-y-6">
        <Link
          to={ROUTES.PROJECTS.LIST}
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Projects</span>
        </Link>

        <ErrorBanner
          error={error}
          onRetry={fetchVersionsData}
        />

        <div className="p-8 text-center rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
          <div className="w-12 h-12 mx-auto rounded-xl bg-slate-800 flex items-center justify-center text-slate-400">
            <FolderGit2 className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-white">Project Not Found</h3>
            <p className="text-xs text-slate-400">
              The project identifier &quot;{projectId}&quot; does not exist or you do not have permission to view it.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Top Breadcrumb & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          to={ROUTES.PROJECTS.DETAIL(projectId)}
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Project Workspace</span>
        </Link>

        <div className="flex items-center gap-2 flex-wrap">
          <Link
            to={ROUTES.PROJECTS.ARTIFACTS(projectId!)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition-colors"
          >
            <FileUp className="w-3.5 h-3.5 text-slate-400" />
            <span>Manage Artifacts</span>
          </Link>

          <button
            type="button"
            onClick={fetchVersionsData}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition-colors"
            title="Refresh Milestone History"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-xs font-bold text-slate-950 transition-colors shadow-lg shadow-emerald-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Create Milestone Version</span>
          </button>
        </div>
      </div>

      {/* Success Notification Banner */}
      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-3 text-emerald-400 text-xs animate-in fade-in">
          <CheckCircle className="w-4 h-4 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Error Banner */}
      {error && <ErrorBanner error={error} onRetry={fetchVersionsData} />}

      {/* Project Overview Mini-Header */}
      {project && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded">
                {project.public_id}
              </span>
              <LifecycleBadge stage={project.current_lifecycle_stage} />
              <StatusBadge status={project.status} />
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              {project.title}
            </h1>
            <p className="text-xs text-slate-400">
              Department of {project.department} • Academic Year {project.academic_year}
            </p>
          </div>

          <div className="flex items-center gap-3 self-start sm:self-auto text-xs font-mono text-slate-400 bg-slate-950/60 px-4 py-3 rounded-xl border border-slate-800">
            <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <p className="text-slate-500 text-[10px] uppercase">Recorded Milestones</p>
              <p className="text-white font-bold text-sm">{versions.length} Versions</p>
            </div>
          </div>
        </div>
      )}

      {/* Milestone Versions Timeline / Cards List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-emerald-400" />
            <h2 className="text-base font-bold text-white">Milestone Snapshots & Anchoring History</h2>
          </div>
          <span className="text-xs font-mono text-slate-500">
            Ascending Version Index
          </span>
        </div>

        {versions.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-4">
            <div className="w-12 h-12 mx-auto rounded-xl bg-slate-800/60 flex items-center justify-center text-slate-400">
              <Layers className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-white">No Milestone Versions Recorded Yet</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                No milestone version snapshots have been registered for this project. Create the initial version snapshot to anchor proof of ownership.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setIsCreateModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-xs font-bold text-slate-950 transition-colors shadow-lg shadow-emerald-500/20"
            >
              <Plus className="w-4 h-4" />
              <span>Create Initial Milestone Version</span>
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {versions.map((ver) => (
              <ProjectVersionCard
                key={ver.public_id}
                version={ver}
                isExpandedDefault={false}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create Version Modal */}
      {projectId && (
        <CreateVersionModal
          projectId={projectId}
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onSuccess={handleCreateSuccess}
          availableArtifacts={availableArtifacts}
        />
      )}
    </div>
  );
};
