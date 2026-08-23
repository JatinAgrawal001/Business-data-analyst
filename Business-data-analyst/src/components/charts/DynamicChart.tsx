import React, { useState, useEffect, useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { Chart } from '../../types';
import { Download, BarChart2, TrendingUp, PieChart as PieIcon, Layers, Dot } from 'lucide-react';
import { formatNumber, formatLabel } from '../../utils/dataEngine';

interface DynamicChartProps {
  chart: Chart;
  height?: number;
}

const DEFAULT_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#06b6d4', '#ec4899', '#8b5cf6', '#3b82f6', '#14b8a6'];

export const DynamicChart: React.FC<DynamicChartProps> = ({ chart, height = 320 }) => {
  const [activeType, setActiveType] = useState<string>(chart?.chartType || 'line');

  // Synchronize activeType when chart or chartType changes
  useEffect(() => {
    if (chart?.chartType) {
      const type = chart.chartType === 'pie' ? 'donut' : (chart.chartType === 'composed' ? 'bar' : chart.chartType);
      setActiveType(type);
    }
  }, [chart?.chartType, chart?.id]);

  const rawChartData = chart?.data || [];
  const colors = chart?.colors && chart.colors.length > 0 ? chart.colors : DEFAULT_COLORS;

  // Derive keys dynamically from actual data
  const sampleRow = rawChartData[0] || {};
  const dataKeys = Object.keys(sampleRow);

  // 1. Resolve X-Axis Key
  const resolvedXAxisKey = useMemo(() => {
    if (chart?.xAxisKey && dataKeys.includes(chart.xAxisKey)) {
      return chart.xAxisKey;
    }
    // Search for common category/time keys or string-type property
    const stringKey = dataKeys.find((k) => typeof sampleRow[k] === 'string' && k !== 'id');
    if (stringKey) return stringKey;
    return dataKeys[0] || 'category';
  }, [chart?.xAxisKey, dataKeys, sampleRow]);

  // 2. Resolve Y-Axis Keys
  const resolvedYAxisKeys = useMemo(() => {
    const validProvidedKeys = (chart?.yAxisKeys || []).filter(
      (k) => k && rawChartData.some((d) => d[k] !== undefined)
    );
    if (validProvidedKeys.length > 0) {
      return validProvidedKeys;
    }

    // Extract all numeric properties (or convertible to number)
    const numericKeys = dataKeys.filter((k) => {
      if (k === resolvedXAxisKey || k === 'id') return false;
      return rawChartData.some((d) => {
        const val = d[k];
        return typeof val === 'number' || (!isNaN(Number(val)) && val !== null && val !== '');
      });
    });

    if (numericKeys.length > 0) {
      return numericKeys;
    }

    const remainingKeys = dataKeys.filter((k) => k !== resolvedXAxisKey);
    return remainingKeys.length > 0 ? remainingKeys : ['value'];
  }, [chart?.yAxisKeys, dataKeys, rawChartData, resolvedXAxisKey]);

  // 3. Normalize dataset so numerical columns are parsed to numbers
  const chartData = useMemo(() => {
    if (!rawChartData || rawChartData.length === 0) return [];
    return rawChartData.map((row) => {
      const newRow: Record<string, any> = { ...row };
      resolvedYAxisKeys.forEach((key) => {
        if (newRow[key] !== undefined && newRow[key] !== null) {
          const num = Number(newRow[key]);
          if (!isNaN(num)) {
            newRow[key] = num;
          }
        }
      });
      return newRow;
    });
  }, [rawChartData, resolvedYAxisKeys]);

  const downloadCSV = () => {
    if (chartData.length === 0) return;
    const headers = Object.keys(chartData[0]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...chartData.map((row) => headers.map((h) => row[h]).join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${chart?.id || 'chart'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900/95 border border-slate-700 p-3.5 rounded-xl shadow-2xl text-xs backdrop-blur-lg z-50">
          <p className="font-bold text-slate-100 mb-2 pb-1.5 border-b border-slate-800">
            {formatLabel(String(label ?? payload[0]?.payload?.[resolvedXAxisKey] ?? ''))}
          </p>
          {payload.map((entry: any, index: number) => (
            <div key={`item-${index}`} className="flex items-center justify-between gap-6 py-1">
              <span className="flex items-center gap-2 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full ring-2 ring-white/20" style={{ backgroundColor: entry.color || colors[index % colors.length] }} />
                <span>{formatLabel(entry.name || entry.dataKey || '')}:</span>
              </span>
              <span className="font-mono font-bold text-white">
                {typeof entry.value === 'number' ? formatNumber(entry.value, 2) : entry.value}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    if (!chartData || chartData.length === 0) {
      return (
        <div className="h-full flex flex-col items-center justify-center text-xs text-slate-400 gap-2">
          <span className="p-2 rounded-xl bg-white/5 border border-white/10 text-slate-400">No chart data available</span>
        </div>
      );
    }

    switch (activeType) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 15, right: 15, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.6} />
              <XAxis
                dataKey={resolvedXAxisKey}
                stroke="#64748b"
                tick={{ fill: '#cbd5e1', fontSize: 11 }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(val) => {
                  const s = String(val ?? '');
                  return s.length > 12 ? s.slice(0, 10) + '...' : s;
                }}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fill: '#cbd5e1', fontSize: 11 }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(val) => formatNumber(val)}
              />
              <Tooltip content={<CustomTooltip />} />
              {resolvedYAxisKeys.length > 1 && <Legend wrapperStyle={{ fontSize: 12, color: '#cbd5e1', paddingTop: '10px' }} />}
              {resolvedYAxisKeys.map((key, idx) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  name={chart.yAxisLabels?.[idx] || formatLabel(key)}
                  stroke={colors[idx % colors.length]}
                  strokeWidth={3}
                  dot={{ r: 4, fill: colors[idx % colors.length], stroke: '#0f172a', strokeWidth: 1.5 }}
                  activeDot={{ r: 7, stroke: '#ffffff', strokeWidth: 2 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 15, right: 15, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.6} />
              <XAxis
                dataKey={resolvedXAxisKey}
                stroke="#64748b"
                tick={{ fill: '#cbd5e1', fontSize: 11 }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(val) => {
                  const s = String(val ?? '');
                  return s.length > 12 ? s.slice(0, 10) + '...' : s;
                }}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fill: '#cbd5e1', fontSize: 11 }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(val) => formatNumber(val)}
              />
              <Tooltip content={<CustomTooltip />} />
              {resolvedYAxisKeys.length > 1 && <Legend wrapperStyle={{ fontSize: 12, color: '#cbd5e1', paddingTop: '10px' }} />}
              {resolvedYAxisKeys.map((key, idx) => (
                <Bar
                  key={key}
                  dataKey={key}
                  name={chart.yAxisLabels?.[idx] || formatLabel(key)}
                  fill={colors[idx % colors.length]}
                  radius={[6, 6, 0, 0]}
                  minPointSize={4}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 15, right: 15, left: -10, bottom: 5 }}>
              <defs>
                {resolvedYAxisKeys.map((key, idx) => (
                  <linearGradient key={`grad-${key}`} id={`grad-${key}-${idx}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={colors[idx % colors.length]} stopOpacity={0.5} />
                    <stop offset="95%" stopColor={colors[idx % colors.length]} stopOpacity={0.05} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.6} />
              <XAxis
                dataKey={resolvedXAxisKey}
                stroke="#64748b"
                tick={{ fill: '#cbd5e1', fontSize: 11 }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(val) => {
                  const s = String(val ?? '');
                  return s.length > 12 ? s.slice(0, 10) + '...' : s;
                }}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fill: '#cbd5e1', fontSize: 11 }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(val) => formatNumber(val)}
              />
              <Tooltip content={<CustomTooltip />} />
              {resolvedYAxisKeys.length > 1 && <Legend wrapperStyle={{ fontSize: 12, color: '#cbd5e1', paddingTop: '10px' }} />}
              {resolvedYAxisKeys.map((key, idx) => (
                <Area
                  key={key}
                  type="monotone"
                  dataKey={key}
                  name={chart.yAxisLabels?.[idx] || formatLabel(key)}
                  stroke={colors[idx % colors.length]}
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill={`url(#grad-${key}-${idx})`}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'donut':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12, color: '#cbd5e1', paddingTop: '10px' }} />
              <Pie
                data={chartData}
                dataKey={resolvedYAxisKeys[0] || 'value'}
                nameKey={resolvedXAxisKey || 'name'}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={90}
                paddingAngle={4}
                stroke="#0f172a"
                strokeWidth={2}
              >
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        );

      case 'scatter':
        const scatterXKey = resolvedXAxisKey;
        const scatterYKey = resolvedYAxisKeys[0] || 'value';
        const isXNumber = chartData.length > 0 && typeof chartData[0][scatterXKey] === 'number';

        return (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 15, right: 15, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.6} />
              <XAxis
                dataKey={scatterXKey}
                type={isXNumber ? 'number' : 'category'}
                name={formatLabel(scatterXKey)}
                stroke="#64748b"
                tick={{ fill: '#cbd5e1', fontSize: 11 }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(val) => (isXNumber ? formatNumber(val) : String(val))}
              />
              <YAxis
                dataKey={scatterYKey}
                type="number"
                name={formatLabel(scatterYKey)}
                stroke="#64748b"
                tick={{ fill: '#cbd5e1', fontSize: 11 }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(val) => formatNumber(val)}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
              <Scatter
                name={`${formatLabel(scatterXKey)} vs ${formatLabel(scatterYKey)}`}
                data={chartData}
                fill={colors[0]}
              />
            </ScatterChart>
          </ResponsiveContainer>
        );

      default:
        // Default graceful fallback to Bar Chart
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 15, right: 15, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.6} />
              <XAxis
                dataKey={resolvedXAxisKey}
                stroke="#64748b"
                tick={{ fill: '#cbd5e1', fontSize: 11 }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(val) => String(val ?? '')}
              />
              <YAxis
                stroke="#64748b"
                tick={{ fill: '#cbd5e1', fontSize: 11 }}
                tickLine={{ stroke: '#475569' }}
                tickFormatter={(val) => formatNumber(val)}
              />
              <Tooltip content={<CustomTooltip />} />
              {resolvedYAxisKeys.map((key, idx) => (
                <Bar
                  key={key}
                  dataKey={key}
                  name={formatLabel(key)}
                  fill={colors[idx % colors.length]}
                  radius={[6, 6, 0, 0]}
                  minPointSize={4}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <div className="w-full min-w-0 p-4 sm:p-5 rounded-2xl sm:rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-xl shadow-black/20 flex flex-col justify-between transition-all hover:border-indigo-500/30 overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0 flex-1">
          <h4 className="text-sm sm:text-base font-bold text-white font-display tracking-tight truncate">
            {chart?.title || 'Data Visualization'}
          </h4>
          {chart?.subtitle && <p className="text-xs text-slate-300 mt-0.5 line-clamp-2">{chart.subtitle}</p>}
        </div>

        {/* View Switchers and export actions */}
        <div className="flex items-center gap-1 bg-white/5 p-1 rounded-xl border border-white/10 shrink-0">
          <button
            onClick={() => setActiveType('line')}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              activeType === 'line' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Line Chart View"
          >
            <TrendingUp className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setActiveType('bar')}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              activeType === 'bar' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Bar Chart View"
          >
            <BarChart2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setActiveType('area')}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              activeType === 'area' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Area Chart View"
          >
            <Layers className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setActiveType('donut')}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              activeType === 'donut' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Donut / Distribution View"
          >
            <PieIcon className="w-3.5 h-3.5" />
          </button>
          {activeType === 'scatter' && (
            <button
              onClick={() => setActiveType('scatter')}
              className="p-1.5 rounded-lg bg-indigo-600 text-white shadow-sm transition-colors cursor-pointer"
              title="Scatter Plot View"
            >
              <Dot className="w-3.5 h-3.5" />
            </button>
          )}
          <div className="w-[1px] h-4 bg-white/10 mx-0.5" />
          <button
            onClick={downloadCSV}
            className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
            title="Export CSV"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="w-full min-w-0 relative my-1" style={{ height: `${height}px`, minHeight: `${height}px` }}>
        {renderChart()}
      </div>

      {/* Footer Info */}
      <div className="mt-2.5 pt-2.5 border-t border-white/10 flex items-center justify-between text-xs text-slate-400 gap-2">
        <span className="truncate flex-1 text-slate-300 text-[11px]">{chart?.description || ''}</span>
        <span className="font-mono text-[10px] text-indigo-400 uppercase font-semibold bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20 shrink-0">
          {chart?.aggregationType || (activeType === 'scatter' ? 'correlation' : 'aggregate')}
        </span>
      </div>
    </div>
  );
};

