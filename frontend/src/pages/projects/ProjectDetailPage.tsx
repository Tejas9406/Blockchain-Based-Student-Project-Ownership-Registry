import React, { useCallback, useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  FolderGit2,
  Layers,
  ArrowLeft,
  Calendar,
  Tag,
  Building,
  User,
  Users,
  Clock,
  RefreshCw,
  Copy,
  Check,
  FileUp,
} from 'lucide-react';
import { projectService } from '../../services/project.service';
import {
  ProjectSummary,
  ProjectMemberItem,
  ProjectVersionDetail,
  NormalizedApiError,
} from '../../types';
import { normalizeApiError } from '../../utils/error';
import { ROUTES } from '../../constants/routes';
import {
  LifecycleBadge,
  StatusBadge,
  VisibilityBadge,
  AnchoringBadge,
} from '../../components/projects/ProjectStatusBadge';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ErrorBanner } from '../../components/ui/ErrorBanner';

export const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();

  const [project, setProject] = useState<ProjectSummary | null>(null);
  const [members, setMembers] = useState<ProjectMemberItem[]>([]);
  const [versions, setVersions] = useState<ProjectVersionDetail[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<NormalizedApiError | null>(null);
  const [copiedText, setCopiedText] = useState<string | null>(null);

  const fetchProjectDetails = useCallback(async () => {
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
      // 1. Fetch main project details
      const projectData = await projectService.getProject(projectId);
      setProject(projectData);

      // 2. Fetch members and versions concurrently (fail-safe)
      const [membersData, versionsData] = await Promise.allSettled([
        projectService.listMembers(projectId),
        projectService.listVersions(projectId),
      ]);

      if (membersData.status === 'fulfilled') {
        setMembers(membersData.value);
      }
      if (versionsData.status === 'fulfilled') {
        setVersions(versionsData.value);
      }
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProjectDetails();
  }, [fetchProjectDetails]);

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(label);
    setTimeout(() => setCopiedText(null), 2000);
  };

  const formatDate = (isoString?: string) => {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto py-24 px-4 flex justify-center">
        <LoadingSpinner size="lg" message="Loading project workspace..." />
      </div>
    );
  }

  if (error || !project) {
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
          error={error || 'Project not found.'}
          onRetry={fetchProjectDetails}
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
          <Link
            to={ROUTES.PROJECTS.LIST}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
          >
            <span>Return to Project Catalog</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Top Breadcrumb & Controls */}
      <div className="flex items-center justify-between">
        <Link
          to={ROUTES.PROJECTS.LIST}
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Projects</span>
        </Link>

        <div className="flex items-center gap-2 flex-wrap">
          <Link
            to={ROUTES.PROJECTS.ARTIFACTS(project.public_id)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition-colors"
          >
            <FileUp className="w-3.5 h-3.5" />
            <span>Manage Artifacts</span>
          </Link>

          <Link
            to={ROUTES.PROJECTS.VERSIONS(project.public_id)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-xs font-bold text-slate-950 transition-colors shadow-sm"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Milestones & Versions</span>
          </Link>

          <button
            type="button"
            onClick={fetchProjectDetails}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Main Project Overview Card */}
      <div className="p-6 sm:p-8 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl space-y-6">
        {/* Header Bar */}
        <div className="space-y-2 border-b border-slate-800/80 pb-6">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-mono font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded">
              PROJECT ID: {project.public_id}
            </span>
            <VisibilityBadge visibility={project.visibility} />
            <LifecycleBadge stage={project.current_lifecycle_stage} />
            <StatusBadge status={project.status} />
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            {project.title}
          </h1>

          <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
            <span>slug: {project.slug}</span>
            <button
              type="button"
              onClick={() => handleCopy(project.public_id, 'id')}
              className="hover:text-slate-300 transition-colors"
              title="Copy Project ID"
            >
              {copiedText === 'id' ? (
                <Check className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        </div>

        {/* Abstract / Overview */}
        <div className="space-y-2">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Project Overview & Abstract
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed bg-slate-950/40 p-4 rounded-xl border border-slate-800/60">
            {project.abstract || 'No detailed abstract provided for this project.'}
          </p>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-slate-800/80">
          <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800/60 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-400 text-xs font-medium">
              <Tag className="w-3.5 h-3.5 text-slate-500" />
              <span>Domain Category</span>
            </div>
            <p className="text-sm font-semibold text-white">{project.category}</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800/60 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-400 text-xs font-medium">
              <Building className="w-3.5 h-3.5 text-slate-500" />
              <span>Department</span>
            </div>
            <p className="text-sm font-semibold text-white">{project.department}</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800/60 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-400 text-xs font-medium">
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              <span>Academic Year</span>
            </div>
            <p className="text-sm font-semibold text-white">{project.academic_year}</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800/60 space-y-1">
            <div className="flex items-center gap-1.5 text-slate-400 text-xs font-medium">
              <User className="w-3.5 h-3.5 text-slate-500" />
              <span>Project Lead</span>
            </div>
            <p className="text-sm font-semibold text-white">
              {project.owner?.full_name || 'Assigned Lead'}
            </p>
          </div>
        </div>

        {/* Timestamps */}
        <div className="pt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 font-mono">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-600" />
            <span>Created: {formatDate(project.created_at)}</span>
          </div>
          {project.updated_at && (
            <div className="flex items-center gap-1.5">
              <span>Last Modified: {formatDate(project.updated_at)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Team Members Section */}
      <div className="p-6 sm:p-8 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Project Team & Mentors</h2>
              <p className="text-xs text-slate-400">
                Registered authors, student contributors, and faculty mentors.
              </p>
            </div>
          </div>
        </div>

        {members.length === 0 ? (
          <div className="p-6 text-center rounded-xl bg-slate-950/40 border border-slate-800/60 text-xs text-slate-400">
            {project.owner ? (
              <p>Primary Author: <span className="text-white font-semibold">{project.owner.full_name}</span> ({project.owner.public_id})</p>
            ) : (
              <p>No additional team members listed.</p>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {members.map((member) => (
              <div
                key={member.user.public_id}
                className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start justify-between gap-2"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold text-white truncate">
                      {member.user.full_name}
                    </span>
                    {member.is_owner && (
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        LEAD
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 truncate">{member.user.email}</p>
                  <p className="text-[11px] font-mono text-slate-500">{member.role_in_project}</p>
                </div>
                {member.contribution_percentage > 0 && (
                  <span className="text-xs font-mono font-semibold text-emerald-400 shrink-0">
                    {member.contribution_percentage}%
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Milestone Versions Section */}
      <div className="p-6 sm:p-8 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Project Version Milestones</h2>
              <p className="text-xs text-slate-400">
                Recorded milestone history and version snapshots.
              </p>
            </div>
          </div>

          <Link
            to={ROUTES.PROJECTS.VERSIONS(project.public_id)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition-colors"
          >
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
            <span>Manage & Anchor</span>
          </Link>
        </div>

        {versions.length === 0 ? (
          <div className="p-8 text-center rounded-xl bg-slate-950/40 border border-slate-800/60 space-y-3 text-xs text-slate-400">
            <p className="font-semibold text-slate-300">No Milestone Versions Recorded</p>
            <p>
              No milestone versions recorded yet for this project.
            </p>
            <Link
              to={ROUTES.PROJECTS.VERSIONS(project.public_id)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-xs font-bold text-slate-950 transition-colors"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Create Initial Milestone</span>
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {versions.map((ver) => (
              <div
                key={ver.public_id}
                className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-mono font-bold text-white bg-slate-800 px-2 py-0.5 rounded">
                      {ver.version_tag}
                    </span>
                    <span className="text-xs font-semibold text-white truncate">
                      {ver.title}
                    </span>
                    <LifecycleBadge stage={ver.lifecycle_stage} />
                    <AnchoringBadge status={ver.anchoring_status} />
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-slate-400">
                    {ver.registration_id && (
                      <span className="text-emerald-400 font-semibold">
                        {ver.registration_id}
                      </span>
                    )}
                    {ver.composite_sha256 && (
                      <span className="text-slate-500 truncate max-w-xs">
                        SHA-256: {ver.composite_sha256.slice(0, 16)}...
                      </span>
                    )}
                  </div>
                </div>

                <div className="text-xs font-mono text-slate-500 shrink-0">
                  {formatDate(ver.created_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
