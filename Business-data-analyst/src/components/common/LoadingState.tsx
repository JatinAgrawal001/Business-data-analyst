import React from 'react';
import { Loader2, Sparkles } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  subMessage?: string;
  fullScreen?: boolean;
}

export const SkeletonCard: React.FC<{ height?: number | string; className?: string }> = ({
  height = 120,
  className = ''
}) => (
  <div
    style={{ minHeight: typeof height === 'number' ? `${height}px` : height }}
    className={`w-full rounded-2xl bg-white/[0.03] border border-white/5 animate-pulse relative overflow-hidden p-4 flex flex-col justify-between ${className}`}
    aria-hidden="true"
  >
    <div className="space-y-2">
      <div className="w-1/3 h-3.5 bg-white/10 rounded-md" />
      <div className="w-2/3 h-2.5 bg-white/5 rounded-md" />
    </div>
    <div className="w-1/2 h-6 bg-white/10 rounded-lg mt-4" />
  </div>
);

export const SkeletonGrid: React.FC<{ count?: number; height?: number; cols?: string }> = ({
  count = 4,
  height = 120,
  cols = 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'
}) => (
  <div className={`grid ${cols} gap-4 w-full`} aria-busy="true" aria-label="Loading content">
    {Array.from({ length: count }).map((_, i) => (
      <SkeletonCard key={i} height={height} />
    ))}
  </div>
);

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Synthesizing statistical models...',
  subMessage = 'Profiling generic schema distributions & generating neural insights',
  fullScreen = false
}) => {
  const content = (
    <div className="flex flex-col items-center justify-center p-12 text-center" role="status" aria-live="polite">
      <div className="relative mb-5">
        <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center animate-pulse shadow-lg shadow-indigo-500/10">
          <Sparkles className="w-7 h-7 text-indigo-400 animate-spin" />
        </div>
        <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-slate-900 rounded-full flex items-center justify-center border border-slate-700">
          <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
        </div>
      </div>
      <h4 className="text-base font-semibold text-slate-100 font-display">{message}</h4>
      <p className="text-xs text-slate-400 max-w-sm mt-1 leading-relaxed">{subMessage}</p>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="min-h-screen bg-[#0A0B10] flex items-center justify-center">
        {content}
      </div>
    );
  }

  return content;
};
