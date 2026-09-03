import React from 'react';
import { Link } from 'react-router-dom';
import { LucideIcon, ArrowRight } from 'lucide-react';

export interface DashboardActionCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  link: string;
  badge?: string;
  actionText?: string;
  variant?: 'emerald' | 'teal' | 'indigo' | 'amber';
}

export const DashboardActionCard: React.FC<DashboardActionCardProps> = ({
  title,
  description,
  icon: Icon,
  link,
  badge,
  actionText = 'Open Module',
  variant = 'emerald',
}) => {
  const variantStyles = {
    emerald: {
      iconBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 group-hover:bg-emerald-500/20',
      badge: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
      actionText: 'text-emerald-400 group-hover:text-emerald-300',
      hoverBorder: 'hover:border-emerald-500/40',
    },
    teal: {
      iconBg: 'bg-teal-500/10 text-teal-400 border-teal-500/20 group-hover:bg-teal-500/20',
      badge: 'bg-teal-500/10 text-teal-300 border-teal-500/30',
      actionText: 'text-teal-400 group-hover:text-teal-300',
      hoverBorder: 'hover:border-teal-500/40',
    },
    indigo: {
      iconBg: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20 group-hover:bg-indigo-500/20',
      badge: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30',
      actionText: 'text-indigo-400 group-hover:text-indigo-300',
      hoverBorder: 'hover:border-indigo-500/40',
    },
    amber: {
      iconBg: 'bg-amber-500/10 text-amber-400 border-amber-500/20 group-hover:bg-amber-500/20',
      badge: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
      actionText: 'text-amber-400 group-hover:text-amber-300',
      hoverBorder: 'hover:border-amber-500/40',
    },
  }[variant];

  return (
    <Link
      to={link}
      className={`group relative flex flex-col justify-between p-6 rounded-2xl bg-slate-900/60 border border-slate-800 transition-all duration-300 hover:scale-[1.01] hover:shadow-xl hover:shadow-slate-950/60 ${variantStyles.hoverBorder} focus:outline-none focus:ring-2 focus:ring-emerald-500/50`}
    >
      <div className="space-y-4">
        {/* Top Icon & Badge Row */}
        <div className="flex items-center justify-between gap-3">
          <div
            className={`w-12 h-12 rounded-xl border flex items-center justify-center transition-colors ${variantStyles.iconBg}`}
          >
            <Icon className="w-6 h-6" />
          </div>
          {badge && (
            <span
              className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold border ${variantStyles.badge}`}
            >
              {badge}
            </span>
          )}
        </div>

        {/* Title & Description */}
        <div className="space-y-1.5">
          <h3 className="text-base sm:text-lg font-bold text-white group-hover:text-emerald-300 transition-colors">
            {title}
          </h3>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            {description}
          </p>
        </div>
      </div>

      {/* Action Footer */}
      <div className="pt-5 mt-4 border-t border-slate-800/80 flex items-center justify-between">
        <span className={`text-xs font-semibold flex items-center gap-1.5 transition-colors ${variantStyles.actionText}`}>
          <span>{actionText}</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
        </span>
      </div>
    </Link>
  );
};
