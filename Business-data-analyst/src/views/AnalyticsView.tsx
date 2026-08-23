import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { DynamicChart } from '../components/charts/DynamicChart';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import {
  BarChart3,
  TrendingUp,
  PieChart,
  GitCompare,
  Layers,
  Filter,
  Download,
  AlertTriangle,
  Database,
  Plus
} from 'lucide-react';
import { formatNumber } from '../utils/dataEngine';

export const AnalyticsView: React.FC = () => {
  const { currentDataset, datasets, currentAnalysis, setCurrentDatasetById, setCurrentRoute, isLoading } = useApp();
  const [chartFilter, setChartFilter] = useState<'all' | 'line' | 'bar' | 'area' | 'donut'>('all');

  if (isLoading && !currentDataset) {
    return <LoadingState message="Computing multi-variate statistical aggregations..." />;
  }

  if (!currentDataset || !currentAnalysis) {
    return (
      <EmptyState
        title="No Analytics Available"
        description="Select or ingest a dataset to generate dynamic multi-dimensional charts."
        actionLabel="Upload Dataset"
        onAction={() => setCurrentRoute('/datasets/upload')}
      />
    );
  }

  const charts = currentAnalysis.charts || [];
  const filteredCharts =
    chartFilter === 'all'
      ? charts
      : charts.filter((c) => c.chartType === chartFilter);

  const correlationMatrix = currentAnalysis.correlationMatrix || [];
  const anomalies = currentAnalysis.anomalies || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 uppercase font-mono">
              {currentDataset.domain}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Dataset: {currentDataset.name}
            </span>
          </div>
          <h2 className="text-2xl font-bold font-display text-slate-100 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-indigo-400" />
            <span>Deep Visual Analytics & Multi-Variate Profiling</span>
          </h2>
        </div>

        {/* Controls: Dataset Switcher & Chart Filter Pills */}
        <div className="flex flex-wrap items-center gap-3">
          {datasets.length > 1 && (
            <div className="flex items-center gap-1.5 bg-slate-900 px-3 py-1.5 rounded-2xl border border-slate-800">
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

          {/* Chart Filter Pills */}
          <div className="flex items-center gap-1 bg-slate-900 p-1.5 rounded-2xl border border-slate-800">
            {(['all', 'line', 'bar', 'area', 'donut'] as const).map((type) => (
              <button
                key={type}
                onClick={() => setChartFilter(type)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold capitalize transition-colors cursor-pointer ${
                  chartFilter === type
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {type === 'all' ? 'All Visuals' : type}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Dynamic Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {filteredCharts.map((chart) => (
          <DynamicChart key={chart.id} chart={chart} height={320} />
        ))}
      </div>

      {/* Cross-Variable Pearson Correlation Matrix */}
      <div className="p-6 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-xl shadow-black/20">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <GitCompare className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white font-display">
                Pearson Correlation Dependency Matrix
              </h3>
              <p className="text-xs text-slate-300">
                Linear association coefficient across quantitative attributes (r: -1.0 to +1.0)
              </p>
            </div>
          </div>
          <span className="text-[11px] font-mono font-semibold px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-indigo-300">
            {correlationMatrix.length} Feature Pairs Evaluated
          </span>
        </div>

        {correlationMatrix.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {correlationMatrix.map((corr, idx) => {
              const isPositive = corr.coefficient >= 0;
              const absVal = Math.abs(corr.coefficient);
              const strength =
                absVal >= 0.7 ? 'Strong' : absVal >= 0.3 ? 'Moderate' : 'Weak / Neutral';

              return (
                <div
                  key={idx}
                  className="p-4 rounded-2xl bg-white/[0.03] border border-white/10 hover:border-indigo-500/30 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between text-xs text-slate-300 mb-2 font-mono">
                      <span className="truncate max-w-[120px] font-semibold text-white">{corr.colA}</span>
                      <span className="text-indigo-400 font-bold">&harr;</span>
                      <span className="truncate max-w-[120px] font-semibold text-white">{corr.colB}</span>
                    </div>

                    <div className="flex items-baseline justify-between gap-2 mt-2">
                      <span
                        className={`text-2xl font-bold font-mono ${
                          isPositive ? 'text-indigo-400' : 'text-amber-400'
                        }`}
                      >
                        {corr.coefficient > 0 ? `+${corr.coefficient.toFixed(2)}` : corr.coefficient.toFixed(2)}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-white/5 border border-white/10 text-slate-300 uppercase tracking-wider">
                        {strength}
                      </span>
                    </div>

                    {corr.description && (
                      <p className="text-[11px] text-slate-300 mt-2 leading-relaxed line-clamp-2">
                        {corr.description}
                      </p>
                    )}
                  </div>

                  {/* Visual Correlation Bar */}
                  <div className="mt-3 pt-2.5 border-t border-white/10">
                    <div className="flex justify-between text-[10px] text-slate-400 font-mono mb-1">
                      <span>Linear Fit (R²)</span>
                      <span>{(Math.pow(corr.coefficient, 2) * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          isPositive ? 'bg-gradient-to-r from-indigo-500 to-sky-400' : 'bg-gradient-to-r from-amber-500 to-rose-400'
                        }`}
                        style={{ width: `${Math.max(5, absVal * 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/5 text-center">
            <p className="text-sm font-semibold text-slate-300">
              No Multi-Variate Numerical Pairs Detected
            </p>
            <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
              Calculating Pearson correlation requires at least two numerical columns in the dataset. Upload a dataset with 2+ numeric dimensions to view correlation dependency matrix.
            </p>
          </div>
        )}
      </div>

      {/* Outlier & Anomaly Scan */}
      {anomalies.length > 0 && (
        <div className="p-6 rounded-3xl bg-slate-900 border border-slate-800 shadow-md">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-400" />
              <h3 className="text-base font-bold text-slate-100 font-display">
                Detected Outliers & Statistical Anomalies (&gt;1.9&sigma;)
              </h3>
            </div>
            <span className="text-xs text-slate-400">
              {anomalies.length} observations deviated significantly from normal distribution
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead>
                <tr className="bg-slate-950/60 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th className="px-4 py-3 font-semibold">Dimension Column</th>
                  <th className="px-4 py-3 font-semibold">Observed Value</th>
                  <th className="px-4 py-3 font-semibold">Baseline Mean</th>
                  <th className="px-4 py-3 font-semibold">Z-Score Deviation</th>
                  <th className="px-4 py-3 font-semibold">Severity Rating</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {anomalies.map((anom, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-semibold text-slate-200">{anom.column}</td>
                    <td className="px-4 py-3 font-mono text-rose-300 font-bold">
                      {typeof anom.value === 'number' ? formatNumber(anom.value, 2) : anom.value}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-400">
                      {typeof anom.expectedValue === 'number'
                        ? formatNumber(anom.expectedValue, 2)
                        : anom.expectedValue}
                    </td>
                    <td className="px-4 py-3 font-mono text-indigo-400 font-semibold">
                      {typeof anom.deviation === 'number' ? `${anom.deviation.toFixed(2)}σ` : `${anom.deviation}σ`}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                          anom.severity === 'critical' || anom.severity === 'high'
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        }`}
                      >
                        {anom.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
