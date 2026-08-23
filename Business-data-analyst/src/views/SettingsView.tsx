import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Settings, Sliders, Shield, Bell, Key, Database, Sparkles, Check } from 'lucide-react';

export const SettingsView: React.FC = () => {
  const { showToast } = useApp();
  const [anomalyThreshold, setAnomalyThreshold] = useState<number>(1.9);
  const [correlationThreshold, setCorrelationThreshold] = useState<number>(0.65);
  const [autoProfileOnUpload, setAutoProfileOnUpload] = useState<boolean>(true);
  const [confidenceInterval, setConfidenceInterval] = useState<number>(95);
  const [themeMode, setThemeMode] = useState<string>('frosted-glass');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    showToast('success', 'Platform Preferences Saved', 'Statistical modeling parameters updated.');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="p-6 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <Settings className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-2xl font-bold font-display text-white">Platform Settings & Statistical Models</h2>
            <p className="text-xs text-slate-300 mt-0.5">
              Tune mathematical heuristics, sensitivity tolerances, and automated intelligence thresholds
            </p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Statistical Engine Settings */}
        <div className="p-6 rounded-2xl backdrop-blur-xl bg-white/[0.04] border border-white/10 space-y-5">
          <div className="flex items-center gap-2 pb-3 border-b border-white/10">
            <Sliders className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-bold text-white font-display">Statistical Profiling Engine</h3>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-semibold text-slate-200">Z-Score Anomaly Deviation Threshold (σ)</span>
                <span className="font-mono text-indigo-400 font-bold">{anomalyThreshold}σ</span>
              </div>
              <input
                type="range"
                min={1.0}
                max={3.5}
                step={0.1}
                value={anomalyThreshold}
                onChange={(e) => setAnomalyThreshold(Number(e.target.value))}
                className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
              <span className="text-[10px] text-slate-400">
                Outliers with absolute Z-score exceeding {anomalyThreshold} will trigger critical statistical flags.
              </span>
            </div>

            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-semibold text-slate-200">Minimum Pearson Correlation Significance (|r|)</span>
                <span className="font-mono text-indigo-400 font-bold">{correlationThreshold}</span>
              </div>
              <input
                type="range"
                min={0.3}
                max={0.95}
                step={0.05}
                value={correlationThreshold}
                onChange={(e) => setCorrelationThreshold(Number(e.target.value))}
                className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
              <span className="text-[10px] text-slate-400">
                Pairwise linear relationships with correlation coefficient ≥ {correlationThreshold} will be surfaced in findings.
              </span>
            </div>

            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-semibold text-slate-200">Forecast Confidence Band Range</span>
                <span className="font-mono text-indigo-400 font-bold">{confidenceInterval}% Two-Tailed CI</span>
              </div>
              <select
                value={confidenceInterval}
                onChange={(e) => setConfidenceInterval(Number(e.target.value))}
                className="w-full px-3.5 py-2 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                <option value={90}>90% Standard Horizon Interval</option>
                <option value={95}>95% Robust Horizon Interval (Recommended)</option>
                <option value={99}>99% High Certainty Conservative Interval</option>
              </select>
            </div>
          </div>
        </div>

        {/* Ingestion & Automation */}
        <div className="p-6 rounded-2xl backdrop-blur-xl bg-white/[0.04] border border-white/10 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-white/10">
            <Database className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-bold text-white font-display">Automated Ingestion Pipeline</h3>
          </div>

          <label className="flex items-center justify-between p-3.5 rounded-xl bg-white/[0.02] border border-white/5 cursor-pointer hover:bg-white/[0.05] transition-colors">
            <div>
              <span className="text-xs font-semibold text-slate-200 block">
                Automatic Neural Synthesis on Upload
              </span>
              <span className="text-[11px] text-slate-400">
                Immediately trigger full descriptive profiling and forecast generation when files are ingested.
              </span>
            </div>
            <input
              type="checkbox"
              checked={autoProfileOnUpload}
              onChange={(e) => setAutoProfileOnUpload(e.target.checked)}
              className="rounded border-white/20 text-indigo-600 focus:ring-indigo-500 w-4 h-4"
            />
          </label>
        </div>

        {/* Theme Settings */}
        <div className="p-6 rounded-2xl backdrop-blur-xl bg-white/[0.04] border border-white/10 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-white/10">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-bold text-white font-display">Interface Theme</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div
              onClick={() => setThemeMode('frosted-glass')}
              className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                themeMode === 'frosted-glass'
                  ? 'bg-indigo-950/40 border-indigo-500/80 shadow-md'
                  : 'bg-white/5 border-white/10'
              }`}
            >
              <div>
                <span className="text-xs font-bold text-white block">Frosted Glass (Active)</span>
                <span className="text-[11px] text-slate-400">Dark ambient orbs with translucent blurred cards</span>
              </div>
              {themeMode === 'frosted-glass' && <Check className="w-4 h-4 text-indigo-400" />}
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all cursor-pointer flex items-center gap-2"
          >
            <Check className="w-4 h-4" />
            <span>Save Preferences</span>
          </button>
        </div>
      </form>
    </div>
  );
};
