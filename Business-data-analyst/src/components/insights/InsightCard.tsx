import React from 'react';
import { Insight } from '../../types';
import {
  Lightbulb,
  AlertTriangle,
  GitCompare,
  PieChart,
  Activity,
  ArrowUpRight,
  CheckCircle2,
  Sparkles
} from 'lucide-react';
import { formatLabel } from '../../utils/dataEngine';

interface InsightCardProps {
  insight: Insight;
  onExplore?: () => void;
}

export const InsightCard: React.FC<InsightCardProps> = ({ insight, onExplore }) => {
  const getCategoryIcon = (cat: Insight['category']) => {
    switch (cat) {
      case 'anomaly':
        return <AlertTriangle className="w-4 h-4 text-rose-400" />;
      case 'correlation':
        return <GitCompare className="w-4 h-4 text-indigo-400" />;
      case 'distribution':
        return <PieChart className="w-4 h-4 text-amber-400" />;
      case 'trend':
      default:
        return <Activity className="w-4 h-4 text-emerald-400" />;
    }
  };

  const getPriorityBadge = (priority: Insight['priority']) => {
    switch (priority) {
      case 'critical':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20 uppercase tracking-wider">
            Critical
          </span>
        );
      case 'high':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 uppercase tracking-wider">
            High Priority
          </span>
        );
      case 'medium':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/20 uppercase tracking-wider">
            Medium
          </span>
        );
      case 'low':
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-500/10 text-slate-400 border border-slate-500/20 uppercase tracking-wider">
            Informational
          </span>
        );
    }
  };

  return (
    <div className="p-5 rounded-2xl backdrop-blur-xl bg-white/[0.04] border border-white/10 hover:border-white/25 hover:bg-white/[0.06] transition-all duration-200 shadow-lg shadow-black/20 flex flex-col justify-between group">
      <div>
        {/* Top Badges */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
              {getCategoryIcon(insight.category)}
            </div>
            <span className="text-xs font-semibold text-slate-300 capitalize">
              {formatLabel(insight.category)} Insight
            </span>
          </div>

          <div className="flex items-center gap-2">
            {getPriorityBadge(insight.priority)}
            <div className="flex items-center gap-1 text-[11px] font-mono text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20">
              <Sparkles className="w-3 h-3 text-indigo-400" />
              <span>{insight.score}/100</span>
            </div>
          </div>
        </div>

        {/* Title & Description */}
        <h4 className="text-sm font-bold text-white font-display group-hover:text-indigo-300 transition-colors">
          {insight.title}
        </h4>
        <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">{insight.description}</p>

        {/* Key Metrics Pill Chips */}
        {insight.keyMetrics && insight.keyMetrics.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-3.5 pt-3 border-t border-white/10">
            {insight.keyMetrics.map((km, idx) => (
              <div key={idx} className="p-2 rounded-xl bg-white/[0.03] border border-white/5">
                <span className="text-[10px] text-slate-400 block truncate font-mono">{km.label}</span>
                <span className="text-xs font-bold font-mono text-white mt-0.5 block">
                  {km.value}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Suggested Action */}
        {insight.suggestedAction && (
          <div className="mt-3.5 p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-200 flex items-start gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
            <span className="leading-relaxed">{insight.suggestedAction}</span>
          </div>
        )}
      </div>

      {/* Footer Info & Action */}
      <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-1.5 truncate max-w-[200px]">
          <span className="text-[10px] text-slate-400 font-mono">COLS:</span>
          {insight.relevantColumns.map((col) => (
            <span
              key={col}
              className="text-[10px] font-mono px-1.5 py-0.2 bg-white/5 border border-white/10 text-slate-300 rounded truncate"
            >
              {col}
            </span>
          ))}
        </div>

        {onExplore && (
          <button
            onClick={onExplore}
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors cursor-pointer"
          >
            <span>Explore</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
};
