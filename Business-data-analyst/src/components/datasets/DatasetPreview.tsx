import React, { useState } from 'react';
import { Dataset, DatasetColumn } from '../../types';
import {
  Hash,
  Calendar,
  Tag,
  KeyRound,
  FileSpreadsheet,
  CheckCircle,
  HelpCircle,
  BarChart,
  Layers,
  ChevronRight
} from 'lucide-react';
import { formatNumber } from '../../utils/dataEngine';

interface DatasetPreviewProps {
  dataset: Dataset;
  onSelectColumn?: (col: DatasetColumn) => void;
}

export const DatasetPreview: React.FC<DatasetPreviewProps> = ({ dataset, onSelectColumn }) => {
  const columns = dataset?.columns || [];
  const [selectedCol, setSelectedCol] = useState<DatasetColumn | null>(columns[0] || null);

  React.useEffect(() => {
    if (columns.length > 0 && (!selectedCol || !columns.some((c) => c.key === selectedCol.key))) {
      setSelectedCol(columns[0]);
    }
  }, [dataset?.id]);

  const getTypeBadge = (type: DatasetColumn['dataType']) => {
    switch (type) {
      case 'numeric':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <Hash className="w-2.5 h-2.5" /> Numeric
          </span>
        );
      case 'datetime':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Calendar className="w-2.5 h-2.5" /> DateTime
          </span>
        );
      case 'id':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <KeyRound className="w-2.5 h-2.5" /> Unique Identifier
          </span>
        );
      case 'categorical':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Tag className="w-2.5 h-2.5" /> Categorical
          </span>
        );
    }
  };

  return (
    <div className="space-y-5">
      {/* Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        <div className="p-4 rounded-2xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-lg shadow-black/20">
          <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider font-mono">
            Total Observations
          </span>
          <p className="text-xl font-bold font-display text-white mt-1">
            {dataset.rowCount.toLocaleString()}
          </p>
        </div>
        <div className="p-4 rounded-2xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-lg shadow-black/20">
          <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider font-mono">
            Schema Dimensions
          </span>
          <p className="text-xl font-bold font-display text-indigo-400 mt-1">
            {columns.length} Columns
          </p>
        </div>
        <div className="p-4 rounded-2xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-lg shadow-black/20">
          <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider font-mono">
            File Ingestion Format
          </span>
          <p className="text-xl font-bold font-display text-emerald-400 mt-1 uppercase font-mono">
            {dataset.fileType}
          </p>
        </div>
        <div className="p-4 rounded-2xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-lg shadow-black/20">
          <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider font-mono">
            Data Quality Index
          </span>
          <p className="text-xl font-bold font-display text-sky-400 mt-1">
            98.5% Healthy
          </p>
        </div>
      </div>

      {/* Main Schema Dictionary & Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Columns Table */}
        <div className="lg:col-span-2 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-xl shadow-black/20 overflow-hidden">
          <div className="p-4 border-b border-white/10 flex items-center justify-between">
            <h4 className="text-sm font-semibold text-white font-display flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4 text-indigo-400" />
              <span>Inferred Schema & Column Dictionary</span>
            </h4>
            <span className="text-xs text-slate-400 font-mono">{columns.length} dimensions profiled</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead>
                <tr className="bg-white/[0.02] border-b border-white/10 text-slate-400 uppercase tracking-wider text-[10px] font-mono">
                  <th className="px-4 py-3 font-semibold">Column Dimension</th>
                  <th className="px-4 py-3 font-semibold">Inferred Type</th>
                  <th className="px-4 py-3 font-semibold">Distinct</th>
                  <th className="px-4 py-3 font-semibold">Completeness</th>
                  <th className="px-4 py-3 font-semibold text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {columns.map((col) => {
                  const isSelected = selectedCol?.key === col.key;
                  const completeness = col.summary
                    ? Math.round(((col.summary.totalCount - col.summary.nullCount) / col.summary.totalCount) * 100)
                    : 100;

                  return (
                    <tr
                      key={col.key}
                      onClick={() => {
                        setSelectedCol(col);
                        onSelectColumn?.(col);
                      }}
                      className={`hover:bg-white/5 transition-colors cursor-pointer ${
                        isSelected ? 'bg-indigo-500/10 font-medium' : ''
                      }`}
                    >
                      <td className="px-4 py-3">
                        <div className="font-semibold text-white">{col.name}</div>
                        <div className="text-[10px] font-mono text-slate-400">{col.key}</div>
                      </td>
                      <td className="px-4 py-3">{getTypeBadge(col.dataType)}</td>
                      <td className="px-4 py-3 font-mono text-slate-300">
                        {col.summary?.uniqueCount ?? '-'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-emerald-500 rounded-full"
                              style={{ width: `${completeness}%` }}
                            />
                          </div>
                          <span className="text-[10px] font-mono text-slate-400">{completeness}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <ChevronRight
                          className={`w-4 h-4 inline-block ${
                            isSelected ? 'text-indigo-400' : 'text-slate-500'
                          }`}
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Column Statistical Inspector */}
        {selectedCol && (
          <div className="rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 p-5 flex flex-col justify-between shadow-xl shadow-black/20">
            <div>
              <div className="flex items-center justify-between gap-2 mb-3">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                  Statistical Profiling
                </span>
                {getTypeBadge(selectedCol.dataType)}
              </div>

              <h4 className="text-base font-bold text-white font-display">
                {selectedCol.name}
              </h4>
              <p className="text-xs font-mono text-indigo-400 mt-0.5">key: {selectedCol.key}</p>
              {selectedCol.description && (
                <p className="text-xs text-slate-300 mt-2 leading-relaxed bg-white/[0.03] p-2.5 rounded-xl border border-white/5">
                  {selectedCol.description}
                </p>
              )}

              {/* Numeric Descriptive Stats */}
              {selectedCol.dataType === 'numeric' && selectedCol.summary && (
                <div className="mt-4 space-y-3">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 bg-white/[0.03] rounded-xl border border-white/5">
                      <span className="text-[10px] text-slate-400 uppercase block font-mono">Mean (Average)</span>
                      <span className="text-sm font-bold font-mono text-white">
                        {formatNumber(selectedCol.summary.mean ?? 0, 2)}
                      </span>
                    </div>
                    <div className="p-2.5 bg-white/[0.03] rounded-xl border border-white/5">
                      <span className="text-[10px] text-slate-400 uppercase block font-mono">Std Deviation</span>
                      <span className="text-sm font-bold font-mono text-white">
                        ±{formatNumber(selectedCol.summary.stdDev ?? 0, 2)}
                      </span>
                    </div>
                    <div className="p-2.5 bg-white/[0.03] rounded-xl border border-white/5">
                      <span className="text-[10px] text-slate-400 uppercase block font-mono">Minimum</span>
                      <span className="text-sm font-bold font-mono text-white">
                        {formatNumber(selectedCol.summary.min ?? 0, 2)}
                      </span>
                    </div>
                    <div className="p-2.5 bg-white/[0.03] rounded-xl border border-white/5">
                      <span className="text-[10px] text-slate-400 uppercase block font-mono">Maximum</span>
                      <span className="text-sm font-bold font-mono text-white">
                        {formatNumber(selectedCol.summary.max ?? 0, 2)}
                      </span>
                    </div>
                  </div>

                  {/* Distribution Histogram */}
                  {selectedCol.summary.distribution && (
                    <div className="mt-3">
                      <span className="text-[11px] font-semibold text-slate-300 block mb-2 font-mono">
                        Frequency Distribution
                      </span>
                      <div className="space-y-1.5">
                        {selectedCol.summary.distribution.map((d, i) => {
                          const maxCount = Math.max(
                            ...(selectedCol.summary?.distribution?.map((x) => x.count) || [1])
                          );
                          const pct = Math.round((d.count / (maxCount || 1)) * 100);
                          return (
                            <div key={i} className="text-[10px]">
                              <div className="flex justify-between text-slate-400 mb-0.5">
                                <span className="truncate max-w-[120px]">{d.bucket}</span>
                                <span className="font-mono text-indigo-300 font-bold">{d.count}</span>
                              </div>
                              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/5">
                                <div
                                  className="h-full bg-indigo-500 rounded-full"
                                  style={{ width: `${pct}%` }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Categorical Top Frequencies */}
              {(selectedCol.dataType === 'categorical' || selectedCol.dataType === 'boolean') &&
                selectedCol.summary?.topCategories && (
                  <div className="mt-4 space-y-2">
                    <span className="text-[11px] font-semibold text-slate-300 block font-mono">
                      Top Class Frequencies
                    </span>
                    {selectedCol.summary.topCategories.map((cat, i) => (
                      <div key={i} className="p-2.5 bg-white/[0.03] rounded-xl border border-white/5 text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-slate-200 truncate max-w-[140px]">
                            {cat.label}
                          </span>
                          <span className="font-mono text-indigo-400 font-bold">{cat.percentage}%</span>
                        </div>
                        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/5">
                          <div
                            className="h-full bg-indigo-500 rounded-full"
                            style={{ width: `${cat.percentage}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
