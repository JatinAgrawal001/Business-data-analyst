import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { RecommendationCard } from '../components/recommendations/RecommendationCard';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import {
  CheckSquare,
  Sparkles,
  Filter,
  CheckCircle,
  Clock,
  Layers,
  ArrowRight,
  Database
} from 'lucide-react';
import { Recommendation } from '../types';

export const RecommendationsView: React.FC = () => {
  const { currentDataset, datasets, currentAnalysis, setCurrentDatasetById, setCurrentRoute, isLoading } = useApp();
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  if (isLoading && !currentDataset) {
    return <LoadingState message="Synthesizing strategic recommendations..." />;
  }

  if (!currentDataset || !currentAnalysis) {
    return (
      <EmptyState
        title="No Dataset Profiled"
        description="Select or ingest a dataset to generate actionable business strategy recommendations."
        actionText="Upload Dataset"
        onAction={() => setCurrentRoute('/datasets/upload')}
      />
    );
  }

  const allRecs = currentAnalysis.recommendations || [];

  const filteredRecs = allRecs.filter((rec) => {
    if (selectedStatus !== 'all' && rec.status !== selectedStatus) return false;
    if (selectedCategory !== 'all' && rec.category !== selectedCategory) return false;
    return true;
  });

  const implementedCount = allRecs.filter((r) => r.status === 'implemented').length;
  const inReviewCount = allRecs.filter((r) => r.status === 'in_review').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-xl flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider font-mono">
              {currentDataset.domain}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Dataset: <span className="text-slate-200 font-semibold">{currentDataset.name}</span>
            </span>
          </div>
          <h2 className="text-2xl font-bold font-display text-white flex items-center gap-2.5">
            <CheckSquare className="w-6 h-6 text-indigo-400" />
            <span>Prescriptive Action Recommendations</span>
          </h2>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Prioritized tactical roadmaps, projected impact assessments, and step-by-step mitigation plans derived from mathematical findings.
          </p>
        </div>

        {/* Status Counters & Dataset Switcher */}
        <div className="flex flex-wrap items-center gap-3">
          {datasets.length > 1 && (
            <div className="flex items-center gap-1.5 bg-white/[0.04] px-3 py-2 rounded-2xl border border-white/10">
              <Database className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <select
                value={currentDataset.id}
                onChange={(e) => setCurrentDatasetById(e.target.value)}
                className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer pr-1"
              >
                {datasets.map((ds) => (
                  <option key={ds.id} value={ds.id} className="bg-slate-900 text-slate-200">
                    {ds.name} ({ds.rowCount} rows)
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex items-center gap-3 p-3 rounded-2xl bg-white/[0.03] border border-white/10 text-xs">
            <div>
              <span className="text-[10px] uppercase text-slate-400 block font-mono">Active Proposals</span>
              <span className="text-base font-bold font-display text-white">{allRecs.length}</span>
            </div>
            <div className="w-[1px] h-7 bg-white/10" />
            <div>
              <span className="text-[10px] uppercase text-slate-400 block font-mono">In Review</span>
              <span className="text-base font-bold font-mono text-sky-400">{inReviewCount}</span>
            </div>
            <div className="w-[1px] h-7 bg-white/10" />
            <div>
              <span className="text-[10px] uppercase text-slate-400 block font-mono">Implemented</span>
              <span className="text-base font-bold font-mono text-emerald-400">{implementedCount}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="p-4 rounded-2xl backdrop-blur-xl bg-white/[0.03] border border-white/10 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          {(['all', 'new', 'in_review', 'implemented', 'dismissed'] as const).map((st) => (
            <button
              key={st}
              onClick={() => setSelectedStatus(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold capitalize transition-all cursor-pointer ${
                selectedStatus === st
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/25'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="all">All Action Categories</option>
            <option value="Operational Optimization">Operational Optimization</option>
            <option value="Quality & Error Control">Quality & Error Control</option>
            <option value="Resource Allocation">Resource Allocation</option>
            <option value="Risk Mitigation">Risk Mitigation</option>
          </select>
        </div>
      </div>

      {/* Recommendations Grid */}
      {filteredRecs.length === 0 ? (
        <EmptyState
          title="No Matching Recommendations"
          description="No strategy proposals match your selected status filter."
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {filteredRecs.map((rec) => (
            <RecommendationCard key={rec.id} recommendation={rec} />
          ))}
        </div>
      )}
    </div>
  );
};
