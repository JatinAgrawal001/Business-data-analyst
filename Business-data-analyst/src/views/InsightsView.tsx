import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { InsightCard } from '../components/insights/InsightCard';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import {
  BrainCircuit,
  Filter,
  Sparkles,
  AlertTriangle,
  GitCompare,
  PieChart,
  Activity,
  ArrowUpDown,
  Search,
  Database
} from 'lucide-react';
import { Insight } from '../types';

export const InsightsView: React.FC = () => {
  const { currentDataset, datasets, currentAnalysis, setCurrentDatasetById, setCurrentRoute, isLoading } = useApp();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'score' | 'priority'>('score');

  if (isLoading && !currentDataset) {
    return <LoadingState message="Deriving neural statistical findings..." />;
  }

  if (!currentDataset || !currentAnalysis) {
    return (
      <EmptyState
        title="No Dataset Profiled"
        description="Select or ingest a dataset to generate automated statistical insights and anomaly scans."
        actionText="Upload Dataset"
        onAction={() => setCurrentRoute('/datasets/upload')}
      />
    );
  }

  const allInsights = currentAnalysis.insights || [];

  const filteredInsights = allInsights.filter((ins) => {
    if (selectedCategory !== 'all' && ins.category !== selectedCategory) return false;
    if (selectedPriority !== 'all' && ins.priority !== selectedPriority) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = ins.title.toLowerCase().includes(q);
      const matchDesc = ins.description.toLowerCase().includes(q);
      const matchCols = (ins.relevantColumns || []).some((c) => c.toLowerCase().includes(q));
      if (!matchTitle && !matchDesc && !matchCols) return false;
    }
    return true;
  }).sort((a, b) => {
    if (sortBy === 'score') return b.score - a.score;
    const priorityWeight: Record<string, number> = { critical: 4, high: 3, medium: 2, low: 1 };
    return (priorityWeight[b.priority] || 0) - (priorityWeight[a.priority] || 0);
  });

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
            <BrainCircuit className="w-6 h-6 text-indigo-400" />
            <span>Autonomous Statistical Findings</span>
          </h2>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Unsupervised cross-variable dependency scans, Z-score outlier alerts, and distribution skewness detections.
          </p>
        </div>

        {/* Quick Summary Pill & Dataset Switcher */}
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
              <span className="text-[10px] uppercase text-slate-400 block font-mono">Total Insights</span>
              <span className="text-base font-bold font-display text-white">{allInsights.length}</span>
            </div>
            <div className="w-[1px] h-7 bg-white/10" />
            <div>
              <span className="text-[10px] uppercase text-slate-400 block font-mono">Avg Score</span>
              <span className="text-base font-bold font-mono text-indigo-400">
                {Math.round(allInsights.reduce((a, b) => a + b.score, 0) / (allInsights.length || 1))}/100
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-2xl backdrop-blur-xl bg-white/[0.03] border border-white/10 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search insights by metric, column, or keyword..."
            className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="all">All Categories</option>
            <option value="anomaly">Anomalies & Outliers</option>
            <option value="correlation">Correlations</option>
            <option value="trend">Trends & Trajectories</option>
            <option value="distribution">Distributions</option>
          </select>

          {/* Priority Filter */}
          <select
            value={selectedPriority}
            onChange={(e) => setSelectedPriority(e.target.value)}
            className="px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="all">All Priorities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Informational</option>
          </select>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'score' | 'priority')}
            className="px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="score">Sort by AI Score</option>
            <option value="priority">Sort by Priority</option>
          </select>
        </div>
      </div>

      {/* Insights Grid */}
      {filteredInsights.length === 0 ? (
        <EmptyState
          title="No Matching Insights Found"
          description="Try resetting search filters or category parameters."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filteredInsights.map((ins) => (
            <InsightCard
              key={ins.id}
              insight={ins}
              onExplore={() => setCurrentRoute('/analytics', currentDataset.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};
