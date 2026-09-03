import React from 'react';
import { LucideIcon, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

interface PlaceholderPageProps {
  title: string;
  description: string;
  moduleName: string;
  icon?: LucideIcon;
  actionText?: string;
  actionLink?: string;
}

export const PlaceholderPage: React.FC<PlaceholderPageProps> = ({
  title,
  description,
  moduleName,
  icon: Icon = ShieldCheck,
  actionText,
  actionLink,
}) => {
  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl text-center space-y-6">
        <div className="w-14 h-14 mx-auto rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shadow-inner">
          <Icon className="w-7 h-7" />
        </div>

        <div className="space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-slate-950 text-slate-300 border border-slate-800">
            {moduleName}
          </div>
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-white">{title}</h2>
          <p className="max-w-xl mx-auto text-sm text-slate-400 leading-relaxed">{description}</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 max-w-lg mx-auto text-left font-mono text-xs text-slate-400 space-y-1">
          <div className="text-emerald-400 font-semibold">// Architecture Status</div>
          <div>API Service: Integrated & Type-Safe</div>
          <div>Router Path: Active</div>
          <div>Business UI: Ready for Feature Implementation</div>
        </div>

        {actionText && actionLink && (
          <div className="pt-2">
            <Link
              to={actionLink}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-sm font-semibold text-white shadow-lg shadow-emerald-950/50 transition-all"
            >
              {actionText}
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};
