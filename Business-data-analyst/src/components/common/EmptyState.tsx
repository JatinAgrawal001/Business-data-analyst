import React, { ReactNode } from 'react';
import { Database, Plus } from 'lucide-react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  actionText?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionText,
  actionLabel,
  onAction
}) => {
  const label = actionText || actionLabel;
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 my-4">
      <div className="w-12 h-12 rounded-xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-slate-400 mb-4">
        {icon || <Database className="w-6 h-6 text-indigo-400" />}
      </div>
      <h3 className="text-base font-semibold text-slate-200 font-display">{title}</h3>
      <p className="text-xs text-slate-400 max-w-md mt-1.5 leading-relaxed">{description}</p>
      {label && onAction && (
        <button
          onClick={onAction}
          className="mt-5 inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          {label}
        </button>
      )}
    </div>
  );
};
