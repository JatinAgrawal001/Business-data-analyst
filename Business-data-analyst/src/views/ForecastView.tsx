import React from 'react';
import { useApp } from '../context/AppContext';
import { ForecastCard } from '../components/forecast/ForecastCard';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import { TrendingUp, Sparkles, Sliders, ShieldCheck, Zap, Database } from 'lucide-react';

export const ForecastView: React.FC = () => {
  const { currentDataset, datasets, currentAnalysis, setCurrentDatasetById, setCurrentRoute, isLoading } = useApp();

  if (isLoading && !currentDataset) {
    return <LoadingState message="Fitting Holt-Winters predictive time-series models..." />;
  }

  if (!currentDataset || !currentAnalysis) {
    return (
      <EmptyState
        title="No Dataset Profiled"
        description="Select or ingest a dataset with numeric or chronological attributes to project predictive trajectories."
        actionText="Upload Dataset"
        onAction={() => setCurrentRoute('/datasets/upload')}
      />
    );
  }

  const forecasts = currentAnalysis.forecasts && currentAnalysis.forecasts.length > 0
    ? currentAnalysis.forecasts
    : (currentAnalysis.forecast ? [currentAnalysis.forecast] : []);

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
              Confidence Band: <span className="text-emerald-400 font-semibold">95% Two-Tailed CI</span>
            </span>
          </div>
          <h2 className="text-2xl font-bold font-display text-white flex items-center gap-2.5">
            <TrendingUp className="w-6 h-6 text-indigo-400" />
            <span>Ensemble Predictive Horizon & Scenario Simulator</span>
          </h2>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Multi-period lookahead models dynamically selected via automated Akaike Information Criterion (AIC) minimizing Mean Absolute Percentage Error (MAPE).
          </p>
        </div>

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

          <div className="flex items-center gap-2 px-3 py-2 rounded-2xl bg-white/[0.03] border border-white/10 text-xs text-slate-300">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Autonomous Seasonality Adjustment</span>
          </div>
        </div>
      </div>

      {/* Forecast Cards */}
      {forecasts.length === 0 ? (
        <EmptyState
          title="No Predictive Variables Available"
          description="The active dataset does not contain sufficient continuous chronological observations for ensemble forecasting."
        />
      ) : (
        <div className="space-y-6">
          {forecasts.map((fc) => (
            <ForecastCard key={fc.id} forecast={fc} />
          ))}
        </div>
      )}
    </div>
  );
};
