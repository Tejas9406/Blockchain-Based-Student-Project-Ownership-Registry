import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FolderGit2,
  PlusCircle,
  Search,
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';
import { projectService, ListProjectsParams } from '../../services/project.service';
import { ProjectSummary, PaginatedMeta, LifecycleStage, NormalizedApiError } from '../../types';
import { normalizeApiError } from '../../utils/error';
import { ROUTES } from '../../constants/routes';
import { ProjectCard } from '../../components/projects/ProjectCard';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ErrorBanner } from '../../components/ui/ErrorBanner';

export const ProjectsListPage: React.FC = () => {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [meta, setMeta] = useState<PaginatedMeta | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<NormalizedApiError | null>(null);

  // Filter and pagination state
  const [search, setSearch] = useState<string>('');
  const [searchInput, setSearchInput] = useState<string>('');
  const [category, setCategory] = useState<string>('');
  const [department, setDepartment] = useState<string>('');
  const [lifecycleStage, setLifecycleStage] = useState<LifecycleStage | ''>('');
  const [page, setPage] = useState<number>(1);
  const pageSize = 12;

  const fetchProjects = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params: ListProjectsParams = {
        page,
        page_size: pageSize,
      };

      if (search.trim()) params.search = search.trim();
      if (category.trim()) params.category = category.trim();
      if (department.trim()) params.department = department.trim();
      if (lifecycleStage) params.lifecycle_stage = lifecycleStage;

      const response = await projectService.listProjects(params);
      setProjects(response.data);
      setMeta(response.meta);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [page, search, category, department, lifecycleStage]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput);
  };

  const handleClearFilters = () => {
    setSearchInput('');
    setSearch('');
    setCategory('');
    setDepartment('');
    setLifecycleStage('');
    setPage(1);
  };

  const hasActiveFilters = Boolean(search || category || department || lifecycleStage);

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold tracking-wider text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">
              MODULE 2: PROJECTS
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Academic Project Catalog
          </h1>
          <p className="text-sm text-slate-400 max-w-2xl">
            Explore registered student innovations across departments, filter by category and lifecycle stage, and inspect ownership history.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={fetchProjects}
            disabled={isLoading}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-colors disabled:opacity-50"
            title="Refresh projects"
            aria-label="Refresh projects list"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
          <Link
            to={ROUTES.PROJECTS.NEW}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-xs font-semibold text-slate-950 transition-colors shadow-lg shadow-emerald-950/40"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Register Project</span>
          </Link>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <ErrorBanner
          error={error}
          onRetry={fetchProjects}
          onDismiss={() => setError(null)}
        />
      )}

      {/* Search and Filters Bar */}
      <div className="p-4 sm:p-5 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by project title or keywords..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/60 transition-all"
            />
          </div>

          <button
            type="submit"
            className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-sm font-semibold text-white border border-slate-700 transition-colors shrink-0"
          >
            Search
          </button>
        </form>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2 border-t border-slate-800/60">
          <div>
            <label htmlFor="filter-lifecycle" className="block text-[11px] font-medium text-slate-400 mb-1">
              Lifecycle Stage
            </label>
            <select
              id="filter-lifecycle"
              value={lifecycleStage}
              onChange={(e) => {
                setLifecycleStage(e.target.value as LifecycleStage | '');
                setPage(1);
              }}
              className="w-full px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500/60 transition-all"
            >
              <option value="">All Stages</option>
              <option value="IDEA">IDEA</option>
              <option value="DESIGN">DESIGN</option>
              <option value="PROTOTYPE">PROTOTYPE</option>
              <option value="FINAL">FINAL</option>
            </select>
          </div>

          <div>
            <label htmlFor="filter-category" className="block text-[11px] font-medium text-slate-400 mb-1">
              Category
            </label>
            <input
              id="filter-category"
              type="text"
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
              placeholder="Filter by category (e.g. AI, WEB3)"
              className="w-full px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500/60 transition-all"
            />
          </div>

          <div>
            <label htmlFor="filter-department" className="block text-[11px] font-medium text-slate-400 mb-1">
              Department
            </label>
            <input
              id="filter-department"
              type="text"
              value={department}
              onChange={(e) => {
                setDepartment(e.target.value);
                setPage(1);
              }}
              placeholder="Filter by department"
              className="w-full px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500/60 transition-all"
            />
          </div>

          <div className="flex items-end">
            {hasActiveFilters && (
              <button
                type="button"
                onClick={handleClearFilters}
                className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-xs font-semibold text-rose-400 border border-rose-500/20 hover:border-rose-500/40 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
                <span>Reset Filters</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Projects List Content */}
      {isLoading ? (
        <div className="py-20 flex justify-center">
          <LoadingSpinner size="lg" message="Loading project catalog..." />
        </div>
      ) : projects.length === 0 ? (
        /* Empty State */
        <div className="p-12 text-center rounded-2xl bg-slate-900/30 border border-slate-800/60 space-y-4">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-slate-800/80 flex items-center justify-center text-slate-400">
            <FolderGit2 className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-white">
              {hasActiveFilters ? 'No Matching Projects Found' : 'No Projects Registered Yet'}
            </h3>
            <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto">
              {hasActiveFilters
                ? 'No projects match your active search filters. Try adjusting or resetting your filter criteria.'
                : 'Initialize your first academic project container to establish immutable provenance and anchor research milestones.'}
            </p>
          </div>
          <div className="pt-2">
            {hasActiveFilters ? (
              <button
                type="button"
                onClick={handleClearFilters}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
              >
                <Filter className="w-3.5 h-3.5" />
                <span>Clear All Filters</span>
              </button>
            ) : (
              <Link
                to={ROUTES.PROJECTS.NEW}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-xs font-semibold text-slate-950 transition-colors"
              >
                <PlusCircle className="w-4 h-4" />
                <span>Register First Project</span>
              </Link>
            )}
          </div>
        </div>
      ) : (
        /* Projects Grid */
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {projects.map((project) => (
              <ProjectCard key={project.public_id} project={project} />
            ))}
          </div>

          {/* Pagination Controls */}
          {meta && meta.total_pages > 1 && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-800/60 text-xs text-slate-400">
              <div>
                Showing page <span className="font-semibold text-white">{meta.page}</span> of{' '}
                <span className="font-semibold text-white">{meta.total_pages}</span> (
                <span className="font-semibold text-white">{meta.total_items}</span> total projects)
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={!meta.has_prev}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  aria-label="Previous page"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>Previous</span>
                </button>

                <button
                  type="button"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!meta.has_next}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  aria-label="Next page"
                >
                  <span>Next</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
