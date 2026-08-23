import React from 'react';
import { useApp } from '../context/AppContext';
import { SAMPLE_DATASETS } from '../utils/sampleData';
import {
  Sparkles,
  BarChart3,
  BrainCircuit,
  Database,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Zap,
  Layers,
  Code2,
  TableProperties
} from 'lucide-react';

export const LandingView: React.FC = () => {
  const { setCurrentRoute, setCurrentDatasetById, showToast } = useApp();

  const handleQuickStart = async (datasetId: string) => {
    await setCurrentDatasetById(datasetId);
    showToast('success', 'Workspace Initialized', 'Loaded domain-agnostic analysis sandbox.');
    setCurrentRoute('/dashboard');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Top Navigation */}
      <nav className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between border-b border-slate-850">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-sky-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-display font-bold text-lg text-slate-100 tracking-tight">
                InsightFlow
              </span>
              <span className="text-[10px] font-bold px-1.5 py-0.2 bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded">
                AI
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Autonomous Business Data Analyst</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setCurrentRoute('/login')}
            className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-slate-100 transition-colors cursor-pointer"
          >
            Sign In
          </button>
          <button
            onClick={() => setCurrentRoute('/dashboard')}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all cursor-pointer flex items-center gap-1.5"
          >
            <span>Launch Dashboard</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 pt-16 pb-20 text-center relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold mb-6">
          <BrainCircuit className="w-3.5 h-3.5" />
          <span>True Schema-Agnostic Intelligence • No Hardcoded Columns</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold font-display tracking-tight text-slate-100 max-w-4xl mx-auto leading-tight">
          Turn Any Business Dataset Into{' '}
          <span className="bg-gradient-to-r from-indigo-400 via-sky-300 to-emerald-400 bg-clip-text text-transparent">
            Statistical Insights & Forecasts
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto mt-6 leading-relaxed">
          Ingest healthcare telemetry, supply chain logistics, energy sensor feeds, student grades, or SaaS metrics.
          InsightFlow dynamically derives mathematical KPIs, anomaly scans, and Holt-Winters forecasting.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 mt-8">
          <button
            onClick={() => setCurrentRoute('/dashboard')}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-xl shadow-indigo-600/30 transition-all flex items-center gap-2 cursor-pointer"
          >
            <Zap className="w-4 h-4" />
            <span>Open Interactive Analyst</span>
          </button>
          <button
            onClick={() => setCurrentRoute('/datasets/upload')}
            className="px-6 py-3 bg-slate-900 hover:bg-slate-850 text-slate-200 border border-slate-800 rounded-xl text-sm font-semibold transition-all flex items-center gap-2 cursor-pointer"
          >
            <Database className="w-4 h-4 text-indigo-400" />
            <span>Upload Custom Schema</span>
          </button>
        </div>

        {/* Quick Sample Selector */}
        <div className="mt-16 pt-12 border-t border-slate-850 text-left">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-base font-bold text-slate-200 font-display">
                Explore Generic Domain Benchmarks
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Select any dataset below to inspect instant dynamic profiling and AI generation:
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {SAMPLE_DATASETS.map((ds) => (
              <div
                key={ds.id}
                onClick={() => handleQuickStart(ds.id)}
                className="p-4 rounded-2xl bg-slate-900 border border-slate-800 hover:border-indigo-500/60 hover:bg-slate-850 transition-all cursor-pointer group flex flex-col justify-between"
              >
                <div>
                  <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block mb-2 font-mono">
                    {ds.domain.split('&')[0]}
                  </span>
                  <h4 className="text-xs font-bold text-slate-200 font-display group-hover:text-indigo-300 transition-colors">
                    {ds.name}
                  </h4>
                  <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                    {ds.description}
                  </p>
                </div>

                <div className="mt-4 pt-2.5 border-t border-slate-850 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                  <span>{ds.columnCount} dimensions</span>
                  <span className="text-indigo-400 group-hover:translate-x-0.5 transition-transform">
                    Inspect &rarr;
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Pillars */}
      <section className="max-w-7xl mx-auto px-6 py-16 border-t border-slate-850">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4">
              <TableProperties className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-100 font-display">
              Generic Schema Ingestion
            </h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Consumes arbitrary tabular data. Automatically detects continuous variables, discrete classes, timestamps, and keys without assuming sales or revenue conventions.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-100 font-display">
              Autonomous Statistical Engine
            </h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Calculates Pearson dependency matrices, Z-score outlier flags (&gt;1.9&sigma;), multi-variable area distributions, and 95% confidence horizon intervals.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center mb-4">
              <Code2 className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-100 font-display">
              Conversational SQL & In-Chat Visuals
            </h3>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Query your data in plain English. Generates dynamic analytical charts, mathematical explanations, and executable SQL queries in real-time.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-6 py-8 border-t border-slate-850 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-4">
        <div>
          InsightFlow AI &copy; 2026 • Enterprise Autonomous Data Intelligence
        </div>
        <div className="flex items-center gap-4">
          <button onClick={() => setCurrentRoute('/dashboard')} className="hover:text-slate-200">
            Dashboard
          </button>
          <button onClick={() => setCurrentRoute('/projects')} className="hover:text-slate-200">
            Projects
          </button>
          <button onClick={() => setCurrentRoute('/reports')} className="hover:text-slate-200">
            Reports
          </button>
          <button onClick={() => setCurrentRoute('/settings')} className="hover:text-slate-200">
            Settings
          </button>
        </div>
      </footer>
    </div>
  );
};
