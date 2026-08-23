import React from 'react';
import { KPI } from '../../types';
import { TrendingUp, TrendingDown, Minus, Activity, Sparkles } from 'lucide-react';

interface KPICardProps {
  kpi: KPI;
  onClick?: () => void;
}

export const KPICard: React.FC<KPICardProps> = ({ kpi, onClick }) => {
  const isUp = kpi.trend === 'up';
  const isDown = kpi.trend === 'down';

  // Render minimal SVG sparkline
  const renderSparkline = (data?: number[]) => {
    if (!data || data.length < 2) return null;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const width = 80;
    const height = 26;

    const points = data
      .map((val, idx) => {
        const x = (idx / (data.length - 1)) * width;
        const y = height - ((val - min) / range) * (height - 6) - 3;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');

    const strokeColor = kpi.isPositive ? '#10b981' : '#f43f5e';
    const fillColor = kpi.isPositive ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)';

    return (
      <div className="shrink-0 flex items-center">
        <svg width={width} height={height} className="overflow-visible">
          <polyline
            fill="none"
            stroke={strokeColor}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
          />
        </svg>
      </div>
    );
  };

  return (
    <div
      onClick={onClick}
      className={`p-5 rounded-2xl backdrop-blur-xl bg-white/[0.04] border border-white/10 hover:border-white/25 hover:bg-white/[0.06] transition-all duration-200 shadow-lg shadow-black/20 relative overflow-hidden group ${
        onClick ? 'cursor-pointer' : ''
      }`}
    >
      {/* Background soft glow accent */}
      <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none group-hover:bg-indigo-500/20 transition-colors" />

      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-300 truncate max-w-[170px]">
            {kpi.label}
          </span>
        </div>

        {/* Delta badge */}
        <div
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold ${
            kpi.isPositive
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
          }`}
        >
          {isUp && <TrendingUp className="w-3 h-3" />}
          {isDown && <TrendingDown className="w-3 h-3" />}
          {!isUp && !isDown && <Minus className="w-3 h-3" />}
          <span>{kpi.changePercentage > 0 ? `+${kpi.changePercentage}` : kpi.changePercentage}%</span>
        </div>
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <div className="min-w-0">
          <div className="text-2xl font-bold font-display text-white tracking-tight flex items-baseline gap-1.5">
            <span>{kpi.value}</span>
            {kpi.unit && <span className="text-xs font-normal text-slate-400">{kpi.unit}</span>}
          </div>
          <p className="text-[11px] text-slate-300 mt-1 truncate max-w-[220px]">
            {kpi.description}
          </p>
        </div>

        {renderSparkline(kpi.sparklineData)}
      </div>

      {kpi.primaryColumn && (
        <div className="mt-3 pt-2.5 border-t border-white/10 flex items-center justify-between text-[10px] text-slate-400 font-mono">
          <span className="truncate">col: {kpi.primaryColumn}</span>
          <span className="text-indigo-400 font-medium">{kpi.category}</span>
        </div>
      )}
    </div>
  );
};
