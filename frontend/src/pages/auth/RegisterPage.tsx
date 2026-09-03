import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus, Lock, Mail, User, Building, Landmark, BookOpen, Wallet, CheckCircle2 } from 'lucide-react';
import { ROUTES } from '../../constants/routes';
import { useAuth } from '../../hooks';
import { ErrorBanner } from '../../components/ui/ErrorBanner';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { NormalizedApiError } from '../../types';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    institution_id: '',
    institution_name: '',
    department: '',
    wallet_address: '',
  });

  const [validationError, setValidationError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<NormalizedApiError | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setValidationError(null);
    setApiError(null);

    const full_name = formData.full_name.trim();
    const email = formData.email.trim();
    const password = formData.password;
    const institution_id = formData.institution_id.trim();
    const institution_name = formData.institution_name.trim();
    const department = formData.department.trim();
    const wallet_address = formData.wallet_address.trim();

    if (!full_name || full_name.length < 2) {
      setValidationError('Full Name is required (minimum 2 characters).');
      return;
    }

    if (!email || !email.includes('@') || !email.includes('.')) {
      setValidationError('Please enter a valid institutional or personal email address.');
      return;
    }

    if (!password || password.length < 8) {
      setValidationError('Password must be at least 8 characters long.');
      return;
    }

    if (!institution_id || institution_id.length < 2) {
      setValidationError('Institutional ID is required (e.g. Student/Roll Number).');
      return;
    }

    if (!department || department.length < 2) {
      setValidationError('Academic department is required (e.g. Computer Science).');
      return;
    }

    if (wallet_address && (!wallet_address.startsWith('0x') || wallet_address.length !== 42)) {
      setValidationError('Optional wallet address must be a valid 42-character EVM address starting with 0x.');
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        full_name,
        email,
        password,
        institution_id,
        institution_name: institution_name || undefined,
        department,
        wallet_address: wallet_address || undefined,
      });

      setIsSuccess(true);
      setTimeout(() => {
        navigate(ROUTES.LOGIN, { replace: true });
      }, 2000);
    } catch (err) {
      setApiError(err as NormalizedApiError);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="max-w-md mx-auto py-16 px-4 text-center">
        <div className="p-8 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-2xl space-y-4">
          <div className="w-14 h-14 mx-auto rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-white">Registration Successful!</h2>
          <p className="text-xs text-slate-300 leading-relaxed">
            Your student account has been created. Redirecting to the sign-in portal...
          </p>
          <div className="pt-2">
            <Link
              to={ROUTES.LOGIN}
              className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 underline"
            >
              Click here if you are not redirected automatically
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto py-10 px-4">
      <div className="p-8 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-2xl space-y-6 backdrop-blur-sm">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 mx-auto rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center text-white shadow-lg shadow-emerald-950/50">
            <UserPlus className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Create Account</h2>
          <p className="text-xs text-slate-400">
            Register your student identity to publish and anchor intellectual project assets.
          </p>
        </div>

        {/* Validation Error Banner */}
        {validationError && (
          <ErrorBanner
            error={{
              status: 400,
              code: 'VALIDATION_ERROR',
              message: validationError,
            }}
            onDismiss={() => setValidationError(null)}
          />
        )}

        {/* API Error Banner */}
        {apiError && (
          <ErrorBanner
            error={apiError}
            onDismiss={() => setApiError(null)}
          />
        )}

        {/* Registration Form */}
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          {/* Full Name */}
          <div className="space-y-1.5">
            <label
              htmlFor="full_name"
              className="block text-xs font-semibold text-slate-300 uppercase tracking-wider"
            >
              Full Legal Name <span className="text-rose-400">*</span>
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                <User className="w-4 h-4" />
              </div>
              <input
                id="full_name"
                name="full_name"
                type="text"
                required
                disabled={isSubmitting}
                value={formData.full_name}
                onChange={handleChange}
                placeholder="Tejas Sharma"
                className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors disabled:opacity-60"
              />
            </div>
          </div>

          {/* Email */}
          <div className="space-y-1.5">
            <label
              htmlFor="email"
              className="block text-xs font-semibold text-slate-300 uppercase tracking-wider"
            >
              Email Address <span className="text-rose-400">*</span>
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                <Mail className="w-4 h-4" />
              </div>
              <input
                id="email"
                name="email"
                type="email"
                required
                disabled={isSubmitting}
                value={formData.email}
                onChange={handleChange}
                placeholder="student@institution.edu"
                className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors disabled:opacity-60"
              />
            </div>
          </div>

          {/* Password */}
          <div className="space-y-1.5">
            <label
              htmlFor="password"
              className="block text-xs font-semibold text-slate-300 uppercase tracking-wider"
            >
              Password <span className="text-rose-400">*</span>
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                <Lock className="w-4 h-4" />
              </div>
              <input
                id="password"
                name="password"
                type="password"
                required
                disabled={isSubmitting}
                value={formData.password}
                onChange={handleChange}
                placeholder="Min. 8 characters"
                className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors disabled:opacity-60"
              />
            </div>
          </div>

          {/* Institutional Info Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Institution ID */}
            <div className="space-y-1.5">
              <label
                htmlFor="institution_id"
                className="block text-xs font-semibold text-slate-300 uppercase tracking-wider"
              >
                Student / Roll ID <span className="text-rose-400">*</span>
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Building className="w-4 h-4" />
                </div>
                <input
                  id="institution_id"
                  name="institution_id"
                  type="text"
                  required
                  disabled={isSubmitting}
                  value={formData.institution_id}
                  onChange={handleChange}
                  placeholder="CS-2026-081"
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors disabled:opacity-60"
                />
              </div>
            </div>

            {/* Department */}
            <div className="space-y-1.5">
              <label
                htmlFor="department"
                className="block text-xs font-semibold text-slate-300 uppercase tracking-wider"
              >
                Department <span className="text-rose-400">*</span>
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <BookOpen className="w-4 h-4" />
                </div>
                <input
                  id="department"
                  name="department"
                  type="text"
                  required
                  disabled={isSubmitting}
                  value={formData.department}
                  onChange={handleChange}
                  placeholder="Computer Science"
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors disabled:opacity-60"
                />
              </div>
            </div>
          </div>

          {/* Institution Name (Optional) */}
          <div className="space-y-1.5">
            <label
              htmlFor="institution_name"
              className="block text-xs font-semibold text-slate-300 uppercase tracking-wider"
            >
              Institution Name <span className="text-slate-500 text-[10px] lowercase">(optional)</span>
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                <Landmark className="w-4 h-4" />
              </div>
              <input
                id="institution_name"
                name="institution_name"
                type="text"
                disabled={isSubmitting}
                value={formData.institution_name}
                onChange={handleChange}
                placeholder="National Institute of Technology"
                className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors disabled:opacity-60"
              />
            </div>
          </div>

          {/* Wallet Address (Optional) */}
          <div className="space-y-1.5">
            <label
              htmlFor="wallet_address"
              className="block text-xs font-semibold text-slate-300 uppercase tracking-wider"
            >
              EVM Wallet Address <span className="text-slate-500 text-[10px] lowercase">(optional)</span>
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                <Wallet className="w-4 h-4" />
              </div>
              <input
                id="wallet_address"
                name="wallet_address"
                type="text"
                disabled={isSubmitting}
                value={formData.wallet_address}
                onChange={handleChange}
                placeholder="0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
                className="w-full pl-10 pr-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-100 font-mono placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors disabled:opacity-60 text-xs"
              />
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-4 inline-flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-sm font-semibold text-white shadow-lg shadow-emerald-950/50 transition-all disabled:opacity-60 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-slate-900"
          >
            {isSubmitting ? (
              <LoadingSpinner size="sm" message="Creating student account..." />
            ) : (
              <>
                <UserPlus className="w-4 h-4" />
                <span>Register Account</span>
              </>
            )}
          </button>
        </form>

        {/* Footer Link */}
        <div className="text-center text-xs text-slate-400 pt-2 border-t border-slate-800/80">
          Already registered?{' '}
          <Link
            to={ROUTES.LOGIN}
            className="text-emerald-400 hover:text-emerald-300 font-semibold underline underline-offset-4 transition-colors"
          >
            Sign In to your Account
          </Link>
        </div>
      </div>
    </div>
  );
};
