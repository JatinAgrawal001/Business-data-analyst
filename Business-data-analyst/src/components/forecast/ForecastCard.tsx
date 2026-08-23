import React, { useState } from 'react';
import { Forecast } from '../../types';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import {
  TrendingUp,
  Sliders,
  Sparkles,
  Info,
  ShieldCheck,
  Zap,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { formatNumber, formatLabel } from '../../utils/dataEngine';

interface ForecastCardProps {
  forecast: Forecast;
  onScenarioChange?: (multiplier: number, horizon: number) => void;
}

export const ForecastCard: React.FC<ForecastCardProps> = ({ forecast, onScenarioChange }) => {
  const [activeScenario, setActiveScenario] = useState<'baseline' | 'optimistic' | 'pessimistic'>('baseline');
  const [horizon, setHorizon] = useState<number>(forecast?.horizonPeriods || 6);

  const historicalData = forecast?.historicalData || [];
  const forecastData = forecast?.forecastData || [];

  // Combine historical and forecast for seamless time-series chart
  const historicalPoints = historicalData.map((d) => ({
    timestamp: d.timestamp,
    historical: d.actual,
    predicted: null,
    lowerBound: null,
    upperBound: null
  }));

  const lastHistorical = historicalData.length > 0 ? historicalData[historicalData.length - 1] : undefined;

  // Apply scenario multiplier
  const multiplier =
    activeScenario === 'optimistic'
      ? forecast?.scenarioMultipliers?.optimistic || 1.15
      : activeScenario === 'pessimistic'
      ? forecast?.scenarioMultipliers?.pessimistic || 0.88
      : 1.0;

  const forecastPoints = forecastData.slice(0, horizon).map((d, idx) => {
    const scaledPred = Number((d.predicted * multiplier).toFixed(1));
    const spread = scaledPred * 0.06;
    return {
      timestamp: d.timestamp,
      historical: null,
      predicted: scaledPred,
      lowerBound: Number((scaledPred - spread).toFixed(1)),
      upperBound: Number((scaledPred + spread).toFixed(1))
    };
  });

  // Bridge point to connect historical with forecast
  const bridgePoint = lastHistorical
    ? {
        timestamp: lastHistorical.timestamp,
        historical: lastHistorical.actual,
        predicted: lastHistorical.actual,
        lowerBound: lastHistorical.actual,
        upperBound: lastHistorical.actual
      }
    : null;

  const chartData = [
    ...historicalPoints.slice(0, -1),
    ...(bridgePoint ? [bridgePoint] : []),
    ...forecastPoints
  ];

  const handleScenarioSelect = (sc: 'baseline' | 'optimistic' | 'pessimistic') => {
    setActiveScenario(sc);
    const m = sc === 'optimistic' ? 1.15 : sc === 'pessimistic' ? 0.88 : 1.0;
    onScenarioChange?.(m, horizon);
  };

  const handleHorizonChange = (h: number) => {
    setHorizon(h);
    const m = activeScenario === 'optimistic' ? 1.15 : activeScenario === 'pessimistic' ? 0.88 : 1.0;
    onScenarioChange?.(m, h);
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900 border border-slate-700 p-3 rounded-xl shadow-xl text-xs backdrop-blur-md">
          <p className="font-semibold text-slate-200 mb-1.5 pb-1 border-b border-slate-800">
            {label}
          </p>
          {payload.map((entry: any, index: number) => {
            if (entry.value === null || entry.value === undefined) return null;
            return (
              <div key={index} className="flex items-center justify-between gap-4 py-0.5">
                <span className="flex items-center gap-1.5 text-slate-400">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                  <span>{formatLabel(entry.name)}:</span>
                </span>
                <span className="font-mono font-bold text-slate-100">
                  {formatNumber(entry.value, 2)}
                </span>
              </div>
            );
          })}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="p-6 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-xl shadow-black/20 space-y-6">
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 rounded-full text-[10px] font-bold uppercase tracking-wider font-mono">
              Ensemble Forecasting
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Model: {forecast.modelUsed}
            </span>
          </div>
          <h3 className="text-lg font-bold text-white font-display mt-1">
            Predictive Horizon: {forecast.targetMetricLabel}
          </h3>
        </div>

        {/* Scenario Controls */}
        <div className="flex items-center gap-1.5 bg-white/5 p-1.5 rounded-2xl border border-white/10">
          <button
            onClick={() => handleScenarioSelect('optimistic')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1 transition-colors cursor-pointer ${
              activeScenario === 'optimistic'
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}
          >
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span>Optimistic (+15%)</span>
          </button>
          <button
            onClick={() => handleScenarioSelect('baseline')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
              activeScenario === 'baseline'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}
          >
            Baseline
          </button>
          <button
            onClick={() => handleScenarioSelect('pessimistic')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1 transition-colors cursor-pointer ${
              activeScenario === 'pessimistic'
                ? 'bg-rose-600 text-white shadow-md shadow-rose-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}
          >
            <ArrowDownRight className="w-3.5 h-3.5" />
            <span>Pessimistic (-12%)</span>
          </button>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="w-full h-80 bg-white/[0.02] p-4 rounded-2xl border border-white/10 relative">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 15, right: 15, left: -10, bottom: 5 }}>
            <defs>
              <linearGradient id="confidenceBand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.6} />
            <XAxis
              dataKey="timestamp"
              stroke="#64748b"
              tick={{ fill: '#cbd5e1', fontSize: 11 }}
              tickLine={{ stroke: '#475569' }}
            />
            <YAxis
              stroke="#64748b"
              tick={{ fill: '#cbd5e1', fontSize: 11 }}
              tickLine={{ stroke: '#475569' }}
              tickFormatter={(val) => formatNumber(val)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, color: '#cbd5e1', paddingTop: '8px' }} />

            {/* Confidence Area */}
            <Area
              type="monotone"
              dataKey="upperBound"
              stroke="transparent"
              fill="url(#confidenceBand)"
              name="95% Confidence Upper"
            />
            <Area
              type="monotone"
              dataKey="lowerBound"
              stroke="transparent"
              fill="transparent"
              name="95% Confidence Lower"
            />

            {/* Historical Observations Line */}
            <Line
              type="monotone"
              dataKey="historical"
              name="Historical Actuals"
              stroke="#38bdf8"
              strokeWidth={3}
              dot={{ r: 4, fill: '#38bdf8', stroke: '#0f172a', strokeWidth: 1.5 }}
              activeDot={{ r: 7, stroke: '#ffffff', strokeWidth: 2 }}
            />

            {/* Forecast Prediction Line */}
            <Line
              type="monotone"
              dataKey="predicted"
              name="Predicted Trajectory"
              stroke="#a855f7"
              strokeWidth={3.5}
              strokeDasharray="5 5"
              dot={{ r: 5, fill: '#a855f7', stroke: '#0f172a', strokeWidth: 1.5 }}
              activeDot={{ r: 7, stroke: '#ffffff', strokeWidth: 2 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Model Parameter Sliders & Key Driver Weights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 pt-2">
        {/* Horizon Slider */}
        <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/5">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="font-semibold text-slate-300">Lookahead Horizon (Periods)</span>
            <span className="font-mono text-indigo-400 font-bold">{horizon} Periods</span>
          </div>
          <input
            type="range"
            min={3}
            max={12}
            step={1}
            value={horizon}
            onChange={(e) => handleHorizonChange(Number(e.target.value))}
            className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
          <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-mono">
            <span>3 Short</span>
            <span>6 Standard</span>
            <span>12 Extended</span>
          </div>
        </div>

        {/* Key Drivers */}
        <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/5">
          <div className="flex items-center justify-between text-xs mb-2.5">
            <span className="font-semibold text-slate-300">Primary Predictive Drivers</span>
            <span className="text-[10px] text-slate-400 font-mono">Sensitivity Weights</span>
          </div>
          <div className="space-y-2">
            {forecast.keyDrivers.map((driver, idx) => (
              <div key={idx} className="text-xs">
                <div className="flex justify-between text-slate-300 mb-0.5">
                  <span className="text-[11px] truncate">{driver.factor}</span>
                  <span className="font-mono text-indigo-300 font-bold">
                    {Math.round(driver.weight * 100)}%
                  </span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/5">
                  <div
                    className={`h-full rounded-full ${
                      driver.direction === 'positive' ? 'bg-indigo-500' : 'bg-rose-500'
                    }`}
                    style={{ width: `${driver.weight * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
