import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { FolderGit2, FileCode, Layers } from 'lucide-react';
import { ROUTES } from '../../constants/routes';

export const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();

  return (
    <div className="max-w-5xl mx-auto py-10 px-4 space-y-8">
      <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <FolderGit2 className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-mono text-slate-400">PROJECT ID: {projectId || 'Unknown'}</div>
            <h2 className="text-2xl font-bold text-white">Project Workspace</h2>
          </div>
        </div>

        <p className="text-sm text-slate-400">
          Manage project details, view team member contributions, upload artifacts, and create anchored milestone snapshots.
        </p>

        <div className="flex flex-wrap gap-3 pt-2">
          <Link
            to={ROUTES.PROJECTS.ARTIFACTS(projectId)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
          >
            <FileCode className="w-4 h-4" />
            <span>Manage Artifacts</span>
          </Link>
          <Link
            to={ROUTES.PROJECTS.VERSIONS(projectId)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white transition-colors"
          >
            <Layers className="w-4 h-4" />
            <span>Milestone Versions</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
