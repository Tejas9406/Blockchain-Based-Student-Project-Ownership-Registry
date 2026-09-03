import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  FileUp,
  FolderGit2,
  RefreshCw,
} from 'lucide-react';
import { projectService } from '../../services/project.service';
import {
  ProjectDetail,
  ProjectVersionDetail,
  ArtifactResponse,
  NormalizedApiError,
} from '../../types';
import { normalizeApiError } from '../../utils/error';
import { ROUTES } from '../../constants/routes';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import {
  ArtifactUploadForm,
  ArtifactList,
} from '../../components/artifacts';

export const ProjectArtifactsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [artifacts, setArtifacts] = useState<ArtifactResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<NormalizedApiError | null>(null);

  const fetchProjectData = useCallback(async () => {
    if (!projectId) return;

    setIsLoading(true);
    setError(null);

    try {
      const [projData, versionsData] = await Promise.all([
        projectService.getProject(projectId),
        projectService.listVersions(projectId).catch(() => [] as ProjectVersionDetail[]),
      ]);

      setProject(projData);

      // Extract any artifacts already embedded in versions
      const initialArtifacts: ArtifactResponse[] = [];
      const seenIds = new Set<string>();

      if (Array.isArray(versionsData)) {
        versionsData.forEach((v) => {
          if (Array.isArray(v.artifacts)) {
            v.artifacts.forEach((art) => {
              if (!seenIds.has(art.public_id)) {
                seenIds.add(art.public_id);
                initialArtifacts.push(art);
              }
            });
          }
        });
      }

      setArtifacts(initialArtifacts);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProjectData();
  }, [fetchProjectData]);

  const handleUploadSuccess = (newArtifact: ArtifactResponse) => {
    setArtifacts((prev) => {
      // Avoid duplicate keys
      if (prev.some((a) => a.public_id === newArtifact.public_id)) {
        return prev;
      }
      return [newArtifact, ...prev];
    });
  };

  if (isLoading && !project) {
    return (
      <div className="py-20 text-center">
        <LoadingSpinner message="Loading project and artifact intake workspace..." />
      </div>
    );
  }

  if (error && !project) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 py-8">
        <div className="flex items-center gap-3">
          <Link
            to={ROUTES.PROJECTS.LIST}
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Projects</span>
          </Link>
        </div>

        <ErrorBanner error={error} onDismiss={() => setError(null)} />

        <div className="text-center pt-4">
          <button
            type="button"
            onClick={fetchProjectData}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry Loading</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {/* Navigation Breadcrumb */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link
          to={projectId ? ROUTES.PROJECTS.DETAIL(projectId) : ROUTES.PROJECTS.LIST}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Project Details</span>
        </Link>

        {project && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-lg">
              {project.public_id}
            </span>
          </div>
        )}
      </div>

      {/* Page Header */}
      <div className="p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/80 to-slate-950 border border-slate-800 space-y-3 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-emerald-400">
              <FolderGit2 className="w-4 h-4" />
              <span>Project Artifact Ingestion</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              {project?.title || 'Project Artifacts'}
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 max-w-2xl">
              Upload source code archives, technical documents, models, and design specifications.
              Files are memory-streamed, SHA-256 hashed, and validated up to 50 MB per file.
            </p>
          </div>
        </div>
      </div>

      {/* Upload Section */}
      <section aria-labelledby="upload-section-heading">
        <h2 id="upload-section-heading" className="sr-only">
          Upload Artifact
        </h2>
        <ArtifactUploadForm
          projectId={project?.public_id || projectId}
          onUploadSuccess={handleUploadSuccess}
        />
      </section>

      {/* Artifacts List Section */}
      <section aria-labelledby="artifacts-list-heading" className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileUp className="w-5 h-5 text-emerald-400" />
            <h2 id="artifacts-list-heading" className="text-lg font-bold text-white tracking-tight">
              Ingested Artifacts ({artifacts.length})
            </h2>
          </div>
        </div>

        <ArtifactList artifacts={artifacts} isLoading={isLoading} />
      </section>
    </div>
  );
};
