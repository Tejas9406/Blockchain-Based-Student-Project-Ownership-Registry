import React from 'react';
import { Loader2 } from 'lucide-react';

export interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  size = 'md',
  className = '',
}) => {
  const iconSizeClass =
    size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-10 h-10' : 'w-8 h-8';

  return (
    <div className={`flex flex-col items-center justify-center p-4 space-y-2 ${className}`}>
      <Loader2 className={`${iconSizeClass} text-emerald-400 animate-spin`} />
      {message && <p className="text-xs text-slate-400 font-medium">{message}</p>}
    </div>
  );
};
