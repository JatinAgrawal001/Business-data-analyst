import React, { useState } from 'react';
import { Recommendation } from '../../types';
import {
  CheckCircle,
  Clock,
  Gauge,
  Layers,
  ChevronDown,
  Sparkles,
  TrendingUp,
  Check
} from 'lucide-react';
import { api } from '../../services/api';
import { useApp } from '../../context/AppContext';

interface RecommendationCardProps {
  recommendation: Recommendation;
  onStatusChange?: (id: string, status: Recommendation['status']) => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onStatusChange
}) => {
  const { showToast } = useApp();
  const [currentStatus, setCurrentStatus] = useState<Recommendation['status']>(recommendation.status);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showStatusMenu, setShowStatusMenu] = useState(false);

  const handleStatusUpdate = async (status: Recommendation['status']) => {
    setCurrentStatus(status);
    setShowStatusMenu(false);
    await api.updateRecommendationStatus(recommendation.id, status);
    showToast('success', 'Recommendation Status Updated', `Marked as ${status.replace('_', ' ')}`);
    onStatusChange?.(recommendation.id, status);
  };

  const getDifficultyBadge = (diff: Recommendation['difficulty']) => {
    switch (diff) {
      case 'easy':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Low Complexity
          </span>
        );
      case 'moderate':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            Moderate Effort
          </span>
        );
      case 'hard':
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            High Complexity
          </span>
        );
    }
  };

  const getStatusBadge = (status: Recommendation['status']) => {
    switch (status) {
      case 'implemented':
        return (
          <span className="px-2.5 py-1 rounded-xl text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
            <CheckCircle className="w-3.5 h-3.5" /> Implemented
          </span>
        );
      case 'in_review':
        return (
          <span className="px-2.5 py-1 rounded-xl text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/30 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" /> In Review
          </span>
        );
      case 'dismissed':
        return (
          <span className="px-2.5 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1.5">
            Dismissed
          </span>
        );
      case 'new':
      default:
        return (
          <span className="px-2.5 py-1 rounded-xl text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" /> New Proposal
          </span>
        );
    }
  };

  return (
    <div className="p-6 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 hover:border-white/25 hover:bg-white/[0.06] transition-all duration-200 shadow-xl shadow-black/20 flex flex-col justify-between">
      <div>
        {/* Header Badges */}
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold px-2.5 py-0.5 bg-white/5 border border-white/10 text-slate-300 rounded-lg">
              {recommendation.category}
            </span>
            {getDifficultyBadge(recommendation.difficulty)}
          </div>

          {/* Status Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowStatusMenu(!showStatusMenu)}
              className="cursor-pointer"
            >
              {getStatusBadge(currentStatus)}
            </button>

            {showStatusMenu && (
              <>
                <div className="fixed inset-0 z-20" onClick={() => setShowStatusMenu(false)} />
                <div className="absolute right-0 mt-2 w-44 backdrop-blur-2xl bg-[#0A0B10]/95 border border-white/10 rounded-2xl shadow-2xl z-30 py-1.5 overflow-hidden">
                  <div className="px-3 py-1.5 text-[10px] font-bold uppercase text-slate-400 border-b border-white/10 font-mono">
                    Change Status
                  </div>
                  {(['new', 'in_review', 'implemented', 'dismissed'] as Recommendation['status'][]).map(
                    (st) => (
                      <button
                        key={st}
                        onClick={() => handleStatusUpdate(st)}
                        className={`w-full text-left px-3 py-1.5 text-xs flex items-center justify-between hover:bg-white/5 cursor-pointer capitalize ${
                          currentStatus === st ? 'text-indigo-400 font-semibold' : 'text-slate-300'
                        }`}
                      >
                        <span>{st.replace('_', ' ')}</span>
                        {currentStatus === st && <Check className="w-3.5 h-3.5 text-indigo-400" />}
                      </button>
                    )
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Title & Summary */}
        <h4 className="text-base font-bold text-white font-display">
          {recommendation.title}
        </h4>
        <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">
          {recommendation.executiveSummary}
        </p>

        {/* Metrics impact & confidence stats */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 my-4 p-3.5 rounded-2xl bg-white/[0.03] border border-white/5">
          <div>
            <span className="text-[10px] text-slate-400 block uppercase font-mono">Projected Impact</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-xs font-bold font-mono text-emerald-400">
                {recommendation.impactScore}/100
              </span>
            </div>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 block uppercase font-mono">AI Confidence</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <Gauge className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-xs font-bold font-mono text-indigo-300">
                {recommendation.confidence}%
              </span>
            </div>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 block uppercase font-mono">Estimated Horizon</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <Clock className="w-3.5 h-3.5 text-sky-400" />
              <span className="text-xs font-bold text-slate-200">{recommendation.timeframe}</span>
            </div>
          </div>
        </div>

        {/* Expected impact quote */}
        <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-200 mb-4">
          <p className="leading-relaxed font-medium">{recommendation.expectedImpact}</p>
        </div>

        {/* Action Steps Checklist */}
        {isExpanded && (
          <div className="space-y-2 mt-4 pt-4 border-t border-white/10">
            <h5 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Step-by-Step Implementation Roadmap
            </h5>
            <div className="space-y-2">
              {recommendation.detailedSteps.map((step, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-2xl bg-white/[0.03] border border-white/5 text-xs text-slate-300 flex items-start gap-2.5"
                >
                  <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <span className="leading-relaxed">{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer Toggle Button */}
      <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-1 text-[11px]">
          <span>Affects:</span>
          {recommendation.metricsInfluenced.map((m) => (
            <span key={m} className="px-2 py-0.5 bg-white/5 border border-white/10 text-slate-300 rounded font-mono text-[10px]">
              {m}
            </span>
          ))}
        </div>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors cursor-pointer"
        >
          <span>{isExpanded ? 'Hide Steps' : 'View Action Steps'}</span>
          <ChevronDown
            className={`w-3.5 h-3.5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          />
        </button>
      </div>
    </div>
  );
};
