import React from 'react';
import { Link } from 'react-router-dom';
import { User, Calendar, Tag, ArrowRight } from 'lucide-react';
import { ProjectSummary } from '../../types';
import { ROUTES } from '../../constants/routes';
import { LifecycleBadge, StatusBadge, VisibilityBadge } from './ProjectStatusBadge';

export interface ProjectCardProps {
  project: ProjectSummary;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({ project }) => {
  const formattedDate = project.created_at
    ? new Date(project.created_at).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : 'Unknown Date';

  return (
    <div className="flex flex-col justify-between p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700/80 hover:bg-slate-900/80 transition-all duration-200 shadow-lg group">
      <div className="space-y-4">
        {/* Top bar: ID and Badges */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
              {project.public_id}
            </span>
            <VisibilityBadge visibility={project.visibility} />
          </div>
          <div className="flex items-center gap-1.5">
            <LifecycleBadge stage={project.current_lifecycle_stage} />
            <StatusBadge status={project.status} />
          </div>
        </div>

        {/* Project Title & Abstract */}
        <div className="space-y-2">
          <h3 className="text-lg font-bold text-white group-hover:text-emerald-300 transition-colors line-clamp-1">
            {project.title}
          </h3>
          {project.abstract && (
            <p className="text-sm text-slate-400 line-clamp-2 leading-relaxed">
              {project.abstract}
            </p>
          )}
        </div>

        {/* Metadata Badges / Info */}
        <div className="pt-2 border-t border-slate-800/60 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-400">
          <div className="flex items-center gap-1.5 truncate">
            <Tag className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span className="truncate">{project.category} • {project.department}</span>
          </div>

          <div className="flex items-center gap-1.5 truncate">
            <Calendar className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span>AY: {project.academic_year}</span>
          </div>

          {project.owner && (
            <div className="flex items-center gap-1.5 truncate sm:col-span-2">
              <User className="w-3.5 h-3.5 text-slate-500 shrink-0" />
              <span className="truncate">Lead: {project.owner.full_name}</span>
            </div>
          )}
        </div>
      </div>

      {/* Footer / Action */}
      <div className="pt-4 mt-4 border-t border-slate-800/60 flex items-center justify-between text-xs">
        <span className="text-slate-500 font-mono">
          Created: {formattedDate}
        </span>
        <Link
          to={ROUTES.PROJECTS.DETAIL(project.public_id)}
          className="inline-flex items-center gap-1.5 font-medium text-emerald-400 hover:text-emerald-300 transition-colors group/link"
          aria-label={`View details for ${project.title}`}
        >
          <span>View Workspace</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover/link:translate-x-0.5 transition-transform" />
        </Link>
      </div>
    </div>
  );
};
