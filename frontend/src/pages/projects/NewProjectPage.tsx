import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  FolderPlus,
  ArrowLeft,
  Loader2,
  Sparkles,
} from 'lucide-react';
import { projectService } from '../../services/project.service';
import { ProjectCreateRequest, NormalizedApiError } from '../../types';
import { normalizeApiError } from '../../utils/error';
import { ROUTES } from '../../constants/routes';
import { useAuth } from '../../context/AuthContext';
import { ErrorBanner } from '../../components/ui/ErrorBanner';

export const NewProjectPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [title, setTitle] = useState('');
  const [abstract, setAbstract] = useState('');
  const [category, setCategory] = useState('');
  const [department, setDepartment] = useState(user?.department || '');
  const [academicYear, setAcademicYear] = useState('2025-2026');
  const [visibility, setVisibility] = useState<'PUBLIC' | 'INSTITUTIONAL' | 'PRIVATE'>('PUBLIC');

  React.useEffect(() => {
    if (user?.department && !department) {
      setDepartment(user.department);
    }
  }, [user?.department]);

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<NormalizedApiError | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const categoryPresets = [
    'AI / Machine Learning',
    'Blockchain & Web3',
    'Cybersecurity',
    'Cloud & Distributed Systems',
    'IoT & Embedded Systems',
    'Data Science & Analytics',
  ];

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!title.trim()) {
      errors.title = 'Project title is required.';
    } else if (title.trim().length < 3) {
      errors.title = 'Title must be at least 3 characters.';
    } else if (title.trim().length > 255) {
      errors.title = 'Title must be 255 characters or fewer.';
    }

    if (!category.trim()) {
      errors.category = 'Category is required.';
    } else if (category.trim().length < 2) {
      errors.category = 'Category must be at least 2 characters.';
    } else if (category.trim().length > 100) {
      errors.category = 'Category must be 100 characters or fewer.';
    }

    if (!department.trim()) {
      errors.department = 'Academic department is required.';
    } else if (department.trim().length < 2) {
      errors.department = 'Department must be at least 2 characters.';
    } else if (department.trim().length > 100) {
      errors.department = 'Department must be 100 characters or fewer.';
    }

    if (!academicYear.trim()) {
      errors.academicYear = 'Academic year is required.';
    } else if (academicYear.trim().length < 4) {
      errors.academicYear = 'Academic year must be at least 4 characters (e.g. 2025-2026).';
    } else if (academicYear.trim().length > 50) {
      errors.academicYear = 'Academic year must be 50 characters or fewer.';
    }

    if (abstract.trim().length > 5000) {
      errors.abstract = 'Abstract must be 5000 characters or fewer.';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError(null);

    if (!validateForm() || isSubmitting) {
      return;
    }

    setIsSubmitting(true);

    try {
      const payload: ProjectCreateRequest = {
        title: title.trim(),
        category: category.trim(),
        department: department.trim(),
        academic_year: academicYear.trim(),
        visibility,
        abstract: abstract.trim() ? abstract.trim() : undefined,
      };

      const createdProject = await projectService.createProject(payload);
      navigate(ROUTES.PROJECTS.DETAIL(createdProject.public_id));
    } catch (err) {
      setApiError(normalizeApiError(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center justify-between">
        <Link
          to={ROUTES.PROJECTS.LIST}
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Projects</span>
        </Link>
      </div>

      {/* Header */}
      <div className="space-y-1 border-b border-slate-800/80 pb-6">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-bold tracking-wider text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">
            MODULE 2: PROJECTS
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Register New Project
        </h1>
        <p className="text-sm text-slate-400">
          Initialize a new academic project container, configure departmental metadata, and assign project leadership.
        </p>
      </div>

      {/* API Error Notification */}
      {apiError && (
        <ErrorBanner
          error={apiError}
          onDismiss={() => setApiError(null)}
        />
      )}

      {/* Form Container */}
      <div className="p-6 sm:p-8 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Project Title */}
          <div className="space-y-1.5">
            <label htmlFor="project-title" className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
              Project Title <span className="text-rose-400">*</span>
            </label>
            <input
              id="project-title"
              type="text"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                if (validationErrors.title) {
                  setValidationErrors((prev) => ({ ...prev, title: '' }));
                }
              }}
              placeholder="e.g. Decentralized IPFS Academic Registry with EVM Anchoring"
              aria-required="true"
              aria-invalid={Boolean(validationErrors.title)}
              className={`w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 transition-all ${
                validationErrors.title
                  ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/50'
                  : 'border-slate-800 focus:border-emerald-500/60 focus:ring-emerald-500/60'
              }`}
            />
            {validationErrors.title && (
              <p className="text-xs text-rose-400 mt-1" role="alert">
                {validationErrors.title}
              </p>
            )}
          </div>

          {/* Category & Department Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Category */}
            <div className="space-y-1.5">
              <label htmlFor="project-category" className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Domain Category <span className="text-rose-400">*</span>
              </label>
              <input
                id="project-category"
                type="text"
                value={category}
                onChange={(e) => {
                  setCategory(e.target.value);
                  if (validationErrors.category) {
                    setValidationErrors((prev) => ({ ...prev, category: '' }));
                  }
                }}
                placeholder="e.g. Blockchain & Web3"
                aria-required="true"
                aria-invalid={Boolean(validationErrors.category)}
                className={`w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 transition-all ${
                  validationErrors.category
                    ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/50'
                    : 'border-slate-800 focus:border-emerald-500/60 focus:ring-emerald-500/60'
                }`}
              />
              {/* Presets */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {categoryPresets.map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => {
                      setCategory(preset);
                      if (validationErrors.category) {
                        setValidationErrors((prev) => ({ ...prev, category: '' }));
                      }
                    }}
                    className="text-[11px] px-2 py-0.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                  >
                    {preset}
                  </button>
                ))}
              </div>
              {validationErrors.category && (
                <p className="text-xs text-rose-400 mt-1" role="alert">
                  {validationErrors.category}
                </p>
              )}
            </div>

            {/* Department */}
            <div className="space-y-1.5">
              <label htmlFor="project-department" className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Department <span className="text-rose-400">*</span>
              </label>
              <input
                id="project-department"
                type="text"
                value={department}
                onChange={(e) => {
                  setDepartment(e.target.value);
                  if (validationErrors.department) {
                    setValidationErrors((prev) => ({ ...prev, department: '' }));
                  }
                }}
                placeholder="e.g. Computer Science & Engineering"
                aria-required="true"
                aria-invalid={Boolean(validationErrors.department)}
                className={`w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 transition-all ${
                  validationErrors.department
                    ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/50'
                    : 'border-slate-800 focus:border-emerald-500/60 focus:ring-emerald-500/60'
                }`}
              />
              {validationErrors.department && (
                <p className="text-xs text-rose-400 mt-1" role="alert">
                  {validationErrors.department}
                </p>
              )}
            </div>
          </div>

          {/* Academic Year & Visibility Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Academic Year */}
            <div className="space-y-1.5">
              <label htmlFor="project-academic-year" className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Academic Year <span className="text-rose-400">*</span>
              </label>
              <input
                id="project-academic-year"
                type="text"
                value={academicYear}
                onChange={(e) => {
                  setAcademicYear(e.target.value);
                  if (validationErrors.academicYear) {
                    setValidationErrors((prev) => ({ ...prev, academicYear: '' }));
                  }
                }}
                placeholder="e.g. 2025-2026"
                aria-required="true"
                aria-invalid={Boolean(validationErrors.academicYear)}
                className={`w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 transition-all ${
                  validationErrors.academicYear
                    ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/50'
                    : 'border-slate-800 focus:border-emerald-500/60 focus:ring-emerald-500/60'
                }`}
              />
              {validationErrors.academicYear && (
                <p className="text-xs text-rose-400 mt-1" role="alert">
                  {validationErrors.academicYear}
                </p>
              )}
            </div>

            {/* Visibility */}
            <div className="space-y-1.5">
              <label htmlFor="project-visibility" className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Visibility Level
              </label>
              <select
                id="project-visibility"
                value={visibility}
                onChange={(e) => setVisibility(e.target.value as 'PUBLIC' | 'INSTITUTIONAL' | 'PRIVATE')}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-sm text-white focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/60 transition-all"
              >
                <option value="PUBLIC">PUBLIC — Discoverable on verification portal</option>
                <option value="INSTITUTIONAL">INSTITUTIONAL — Campus & Evaluators Only</option>
                <option value="PRIVATE">PRIVATE — Restricted to Team Members</option>
              </select>
            </div>
          </div>

          {/* Abstract / Description */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label htmlFor="project-abstract" className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                Project Abstract / Executive Summary
              </label>
              <span className="text-[11px] font-mono text-slate-500">
                {abstract.length} / 5000 chars
              </span>
            </div>
            <textarea
              id="project-abstract"
              rows={5}
              value={abstract}
              onChange={(e) => {
                setAbstract(e.target.value);
                if (validationErrors.abstract) {
                  setValidationErrors((prev) => ({ ...prev, abstract: '' }));
                }
              }}
              placeholder="Provide a comprehensive summary of project problem statement, methodology, architecture, and expected deliverables..."
              className={`w-full px-4 py-3 rounded-xl bg-slate-950/80 border text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 transition-all ${
                validationErrors.abstract
                  ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/50'
                  : 'border-slate-800 focus:border-emerald-500/60 focus:ring-emerald-500/60'
              }`}
            />
            {validationErrors.abstract && (
              <p className="text-xs text-rose-400 mt-1" role="alert">
                {validationErrors.abstract}
              </p>
            )}
          </div>

          {/* Information Notice */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-start gap-3 text-xs text-slate-400">
            <Sparkles className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold text-slate-300">Automatic Ownership Attribution:</span>
              <p>
                Creating this project establishes you ({user?.full_name || 'Current User'}) as the primary project lead and assigns an immutable public registration container on the platform.
              </p>
            </div>
          </div>

          {/* Form Actions */}
          <div className="pt-4 border-t border-slate-800/80 flex flex-col-reverse sm:flex-row items-center justify-end gap-3">
            <Link
              to={ROUTES.PROJECTS.LIST}
              className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 text-center transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-xs font-bold text-slate-950 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-950/40"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Registering Project...</span>
                </>
              ) : (
                <>
                  <FolderPlus className="w-4 h-4" />
                  <span>Register Project</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
