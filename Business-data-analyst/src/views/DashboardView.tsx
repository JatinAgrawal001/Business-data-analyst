import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { KPIGrid } from '../components/kpi/KPIGrid';
import { ChartGrid } from '../components/charts/ChartGrid';
import { InsightCard } from '../components/insights/InsightCard';
import { RecommendationCard } from '../components/recommendations/RecommendationCard';
import { ForecastCard } from '../components/forecast/ForecastCard';
import { AnalysisProgress } from '../components/analysis/AnalysisProgress';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import {
  Sparkles,
  UploadCloud,
  FileSpreadsheet,
  MessageSquare,
  FileText,
  TrendingUp,
  BrainCircuit,
  ArrowRight,
  Database,
  RefreshCw,
  Layers
} from 'lucide-react';

export const DashboardView: React.FC = () => {
  const {
    currentDataset,
    currentAnalysis,
    currentProject,
    datasets,
    setCurrentDatasetById,
    setCurrentRoute,
    refreshAnalysis,
    isLoading
  } = useApp();

  const [isRunningPipeline, setIsRunningPipeline] = useState(false);

  if (isLoading && !currentDataset) {
    return <LoadingState message="Loading dynamic intelligence models..." />;
  }

  if (!currentDataset || !currentAnalysis || datasets.length === 0) {
    return (
      <div className="space-y-8 animate-in fade-in duration-300">
        {/* Welcome Header */}
        <div className="p-8 rounded-3xl backdrop-blur-xl bg-gradient-to-br from-indigo-950/40 via-slate-900/60 to-slate-950/80 border border-indigo-500/20 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 mb-4 font-mono">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Real-Time Business Intelligence</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold font-display text-white tracking-tight">
              Welcome to InsightFlow AI
            </h1>
            <p className="text-sm text-slate-300 mt-3 leading-relaxed">
              Your analytics workspace is set up and ready. Since you haven't uploaded any data yet, start by creating a project or uploading your first CSV/JSON dataset.
            </p>
          </div>
        </div>

        {/* Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 hover:border-indigo-500/40 transition-all flex flex-col justify-between group shadow-xl">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4 group-hover:scale-105 transition-transform">
                <UploadCloud className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white font-display">1. Upload Datasets</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Ingest single or multiple CSV, JSON, or TSV files. The autonomous profiling engine detects types, statistics, and distributions.
              </p>
            </div>
            <button
              onClick={() => setCurrentRoute('/datasets/upload')}
              className="mt-6 w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition-colors flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 cursor-pointer"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Upload First Dataset</span>
            </button>
          </div>

          <div className="p-6 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 hover:border-sky-500/40 transition-all flex flex-col justify-between group shadow-xl">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 mb-4 group-hover:scale-105 transition-transform">
                <Layers className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white font-display">2. Create Project</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Organize your analytical data into workspaces like Clinical Operations, Logistics, SaaS Metrics, or Financial Planning.
              </p>
            </div>
            <button
              onClick={() => setCurrentRoute('/projects/new')}
              className="mt-6 w-full py-2.5 px-4 bg-white/10 hover:bg-white/15 text-white border border-white/15 rounded-xl text-xs font-semibold transition-colors flex items-center justify-center gap-2 cursor-pointer"
            >
              <Layers className="w-4 h-4 text-sky-400" />
              <span>Create Project</span>
            </button>
          </div>

          <div className="p-6 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 hover:border-purple-500/40 transition-all flex flex-col justify-between group shadow-xl">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-4 group-hover:scale-105 transition-transform">
                <BrainCircuit className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white font-display">3. AI Insights & Forecasting</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Once data is uploaded, ask questions in natural language, detect anomalies, and generate predictive regression forecasts.
              </p>
            </div>
            <button
              onClick={() => setCurrentRoute('/datasets/upload')}
              className="mt-6 w-full py-2.5 px-4 bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 rounded-xl text-xs font-semibold transition-colors flex items-center justify-center gap-2 cursor-pointer"
            >
              <ArrowRight className="w-4 h-4" />
              <span>Get Started</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  const handleReRun = () => {
    setIsRunningPipeline(true);
  };

  const handlePipelineComplete = async () => {
    setIsRunningPipeline(false);
    await refreshAnalysis();
  };

  const kpis = currentAnalysis?.kpis || [];
  const charts = currentAnalysis?.charts || [];
  const insights = currentAnalysis?.insights || [];
  const recommendations = currentAnalysis?.recommendations || [];
  const forecasts = currentAnalysis?.forecasts || [];

  return (
    <div className="space-y-6">
      {/* Top Banner / Dataset Context Switcher */}
      <div className="p-6 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5 mb-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider font-mono">
                {currentDataset.domain}
              </span>
              <span className="text-xs text-slate-400">
                Project:{' '}
                <span className="text-slate-200 font-semibold">{currentProject?.name}</span>
              </span>
            </div>
            <h2 className="text-2xl font-bold font-display text-white flex items-center gap-2.5">
              <span>{currentDataset.name}</span>
            </h2>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              {currentDataset.description}
            </p>
          </div>

          {/* Quick Dataset Selector Dropdown */}
          <div className="flex flex-wrap items-center gap-2.5 w-full lg:w-auto">
            <select
              value={currentDataset.id}
              onChange={(e) => setCurrentDatasetById(e.target.value)}
              className="px-3.5 py-2 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              {datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  Switch: {ds.name} ({ds.columnCount} cols)
                </option>
              ))}
            </select>

            <button
              onClick={() => setCurrentRoute('/chat', currentDataset.id)}
              className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Ask AI Analyst</span>
            </button>

            <button
              onClick={() => setCurrentRoute('/datasets/upload')}
              className="px-3.5 py-2 bg-white/5 hover:bg-white/10 text-slate-200 border border-white/10 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer backdrop-blur-md"
            >
              <UploadCloud className="w-3.5 h-3.5 text-indigo-400" />
              <span>Ingest New</span>
            </button>
          </div>
        </div>
      </div>

      {/* Autonomous Intelligence Progress Pipeline */}
      <AnalysisProgress
        isRunning={isRunningPipeline}
        onComplete={handlePipelineComplete}
        onRun={handleReRun}
      />

      {/* Section 1: Dynamic KPIs */}
      <div>
        <div className="flex items-center justify-between mb-3.5">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-slate-100 font-display">
              Autonomous KPI Engine
            </h3>
            <span className="text-xs text-slate-500 font-mono">
              ({kpis.length} Inferred Metrics)
            </span>
          </div>
          <span className="text-xs text-slate-400">
            Computed from {currentDataset.rowCount.toLocaleString()} observations
          </span>
        </div>
        <KPIGrid kpis={kpis} />
      </div>

      {/* Section 2: Visual Chart Engine */}
      <div>
        <div className="flex items-center justify-between mb-3.5">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-slate-100 font-display">
              Visual Trajectories & Multi-Variate Views
            </h3>
          </div>
          <button
            onClick={() => setCurrentRoute('/analytics', currentDataset.id)}
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 cursor-pointer"
          >
            <span>Explore All Charts</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
        <ChartGrid charts={charts.slice(0, 4)} />
      </div>

      {/* Section 3: AI Insights & Strategic Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Insights Column */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-100 font-display flex items-center gap-2">
              <BrainCircuit className="w-4 h-4 text-indigo-400" />
              <span>Statistical Findings</span>
            </h3>
            <button
              onClick={() => setCurrentRoute('/insights', currentDataset.id)}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 cursor-pointer"
            >
              <span>View All ({insights.length})</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="space-y-4">
            {insights.slice(0, 2).map((ins) => (
              <InsightCard
                key={ins.id}
                insight={ins}
                onExplore={() => setCurrentRoute('/insights', currentDataset.id)}
              />
            ))}
          </div>
        </div>

        {/* Recommendations Column */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-100 font-display flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>Recommended Actions</span>
            </h3>
            <button
              onClick={() => setCurrentRoute('/recommendations', currentDataset.id)}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 cursor-pointer"
            >
              <span>View All ({recommendations.length})</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="space-y-4">
            {recommendations.slice(0, 2).map((rec) => (
              <RecommendationCard key={rec.id} recommendation={rec} />
            ))}
          </div>
        </div>
      </div>

      {/* Section 4: Predictive Horizon Forecast */}
      {(currentAnalysis?.forecast || forecasts.length > 0) && (
        <div className="space-y-3.5">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-100 font-display flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-400" />
              <span>Ensemble Lookahead Forecast</span>
            </h3>
            <button
              onClick={() => setCurrentRoute('/forecast', currentDataset.id)}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 cursor-pointer"
            >
              <span>Detailed Forecast Horizon</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <ForecastCard forecast={currentAnalysis?.forecast || forecasts[0]} />
        </div>
      )}
    </div>
  );
};
