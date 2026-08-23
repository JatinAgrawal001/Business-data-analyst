import React, { useState, useMemo } from 'react';
import { Dataset, DatasetColumn } from '../../types';
import {
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Download,
  Eye,
  ChevronLeft,
  ChevronRight,
  Hash,
  Calendar,
  Tag,
  KeyRound,
  Check
} from 'lucide-react';
import { formatNumber } from '../../utils/dataEngine';

interface DataTableProps {
  dataset: Dataset;
  title?: string;
  onRowClick?: (row: Record<string, any>) => void;
}

/**
 * Universal helper to resolve field value across different key formats
 * (key, name, originalName, or case-insensitive matching).
 */
export function getCellValue(row: Record<string, any>, col: DatasetColumn): any {
  if (!row || typeof row !== 'object') return null;
  if (row[col.key] !== undefined && row[col.key] !== null) return row[col.key];
  if (col.name && row[col.name] !== undefined && row[col.name] !== null) return row[col.name];
  if (col.originalName && row[col.originalName] !== undefined && row[col.originalName] !== null) return row[col.originalName];

  // Case-insensitive / whitespace-normalized lookup in row
  const targetKey = col.key?.toLowerCase().replace(/[\s_-]/g, '');
  const targetName = col.name?.toLowerCase().replace(/[\s_-]/g, '');
  const targetOrig = col.originalName?.toLowerCase().replace(/[\s_-]/g, '');

  for (const k of Object.keys(row)) {
    const cleanK = k.toLowerCase().replace(/[\s_-]/g, '');
    if (cleanK === targetKey || cleanK === targetName || cleanK === targetOrig) {
      return row[k];
    }
  }

  return null;
}

export const DataTable: React.FC<DataTableProps> = ({ dataset, title, onRowClick }) => {
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [visibleColumns, setVisibleColumns] = useState<string[]>(
    (dataset?.columns || []).map((c) => c.key)
  );
  const [showColPicker, setShowColPicker] = useState(false);

  const rows = dataset?.sampleRows || [];
  const columns = dataset?.columns || [];

  React.useEffect(() => {
    if (dataset?.columns) {
      setVisibleColumns(dataset.columns.map((c) => c.key));
    }
  }, [dataset?.id]);

  // Filter rows by global search term
  const filteredRows = useMemo(() => {
    if (!search.trim()) return rows;
    const lower = search.toLowerCase();
    return rows.filter((row) =>
      columns.some((col) => {
        const val = getCellValue(row, col);
        return String(val ?? '').toLowerCase().includes(lower);
      })
    );
  }, [rows, columns, search]);

  // Sort filtered rows
  const sortedRows = useMemo(() => {
    if (!sortKey) return filteredRows;
    const sortCol = columns.find((c) => c.key === sortKey);
    if (!sortCol) return filteredRows;

    return [...filteredRows].sort((a, b) => {
      const valA = getCellValue(a, sortCol);
      const valB = getCellValue(b, sortCol);
      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortDir === 'asc' ? valA - valB : valB - valA;
      }
      const strA = String(valA);
      const strB = String(valB);
      return sortDir === 'asc' ? strA.localeCompare(strB) : strB.localeCompare(strA);
    });
  }, [filteredRows, columns, sortKey, sortDir]);

  // Paginated rows
  const totalPages = Math.ceil(sortedRows.length / pageSize) || 1;
  const paginatedRows = useMemo(() => {
    const start = (page - 1) * pageSize;
    return sortedRows.slice(start, start + pageSize);
  }, [sortedRows, page, pageSize]);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      if (sortDir === 'asc') setSortDir('desc');
      else {
        setSortKey(null);
        setSortDir('asc');
      }
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const toggleColumn = (key: string) => {
    if (visibleColumns.includes(key)) {
      if (visibleColumns.length > 1) {
        setVisibleColumns(visibleColumns.filter((k) => k !== key));
      }
    } else {
      setVisibleColumns([...visibleColumns, key]);
    }
  };

  const exportTableCSV = () => {
    const activeCols = columns.filter((c) => visibleColumns.includes(c.key));
    const exportHeaders = activeCols.map((c) => `"${c.name.replace(/"/g, '""')}"`);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [
        exportHeaders.join(','),
        ...sortedRows.map((r) =>
          activeCols.map((col) => `"${String(getCellValue(r, col) ?? '').replace(/"/g, '""')}"`).join(',')
        )
      ].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${(dataset?.name || 'dataset').toLowerCase().replace(/\s+/g, '_')}_data.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const renderTypeIcon = (type: DatasetColumn['dataType']) => {
    switch (type) {
      case 'numeric':
        return <Hash className="w-3 h-3 text-sky-400" />;
      case 'datetime':
        return <Calendar className="w-3 h-3 text-emerald-400" />;
      case 'id':
        return <KeyRound className="w-3 h-3 text-amber-400" />;
      case 'categorical':
      default:
        return <Tag className="w-3 h-3 text-purple-400" />;
    }
  };

  const activeColumns = columns.filter((c) => visibleColumns.includes(c.key));

  return (
    <div className="rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-xl shadow-black/20 overflow-hidden">
      {/* Top Action Bar */}
      <div className="p-4 sm:p-5 border-b border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-white font-display">
            {title || `Raw Observations: ${dataset.name}`}
          </h3>
          <p className="text-xs text-slate-300 mt-0.5">
            Showing {sortedRows.length} observations across {columns.length} schema dimensions
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2 w-full sm:w-auto">
          {/* Search bar */}
          <div className="relative flex-1 sm:w-60">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Search observations..."
              className="w-full pl-8 pr-3 py-1.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          {/* Column Toggle Picker */}
          <div className="relative">
            <button
              onClick={() => setShowColPicker(!showColPicker)}
              className="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Eye className="w-3.5 h-3.5 text-slate-400" />
              <span>Columns ({visibleColumns.length})</span>
            </button>

            {showColPicker && (
              <>
                <div className="fixed inset-0 z-20" onClick={() => setShowColPicker(false)} />
                <div className="absolute right-0 mt-2 w-56 bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl z-30 p-2 max-h-64 overflow-y-auto backdrop-blur-xl">
                  <div className="text-[10px] font-bold uppercase text-slate-400 px-2 py-1 mb-1 border-b border-slate-800 font-mono">
                    Visible Columns
                  </div>
                  {columns.map((col) => {
                    const isVisible = visibleColumns.includes(col.key);
                    return (
                      <button
                        key={col.key}
                        onClick={() => toggleColumn(col.key)}
                        className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl text-xs text-slate-300 hover:bg-white/10 transition-colors cursor-pointer"
                      >
                        <div className="flex items-center gap-1.5 truncate">
                          {renderTypeIcon(col.dataType)}
                          <span className="truncate">{col.name}</span>
                        </div>
                        {isVisible && <Check className="w-3.5 h-3.5 text-indigo-400 shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              </>
            )}
          </div>

          {/* Export CSV */}
          <button
            onClick={exportTableCSV}
            className="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            title="Download CSV"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Export CSV</span>
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-200 border-collapse">
          <thead>
            <tr className="bg-white/[0.02] border-b border-white/10 text-slate-400 uppercase tracking-wider text-[10px] font-mono">
              {activeColumns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className="px-4 py-3 font-semibold cursor-pointer hover:text-white transition-colors select-none"
                >
                  <div className="flex items-center gap-1.5">
                    {renderTypeIcon(col.dataType)}
                    <span>{col.name}</span>
                    {sortKey === col.key ? (
                      sortDir === 'asc' ? (
                        <ArrowUp className="w-3 h-3 text-indigo-400" />
                      ) : (
                        <ArrowDown className="w-3 h-3 text-indigo-400" />
                      )
                    ) : (
                      <ArrowUpDown className="w-3 h-3 text-slate-600 opacity-60" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {paginatedRows.length === 0 ? (
              <tr>
                <td colSpan={activeColumns.length} className="px-4 py-12 text-center text-slate-400 text-xs">
                  No records found in this dataset.
                </td>
              </tr>
            ) : (
              paginatedRows.map((row, idx) => (
                <tr
                  key={`row-${idx}`}
                  onClick={() => onRowClick?.(row)}
                  className={`hover:bg-white/5 transition-colors ${
                    onRowClick ? 'cursor-pointer' : ''
                  }`}
                >
                  {activeColumns.map((col) => {
                    const val = getCellValue(row, col);
                    const isNumeric = col.dataType === 'numeric' && (typeof val === 'number' || (!isNaN(Number(val)) && val !== '' && val !== null));
                    const numVal = isNumeric && typeof val !== 'number' ? Number(val) : val;

                    return (
                      <td key={col.key} className="px-4 py-3 truncate max-w-[220px]">
                        {val === null || val === undefined ? (
                          <span className="text-slate-500 italic font-mono">-</span>
                        ) : isNumeric ? (
                          <span className="font-mono font-medium text-slate-100">{formatNumber(numVal, 2)}</span>
                        ) : col.dataType === 'id' ? (
                          <span className="font-mono text-amber-300 font-medium">{String(val)}</span>
                        ) : col.dataType === 'datetime' ? (
                          <span className="text-emerald-300 font-mono">{String(val)}</span>
                        ) : (
                          <span className="text-slate-200">{String(val)}</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-4 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <span>Rows per page:</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="bg-slate-900 border border-white/10 rounded-lg px-2 py-1 text-slate-200 text-xs focus:outline-none cursor-pointer"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          <span className="text-slate-600">|</span>
          <span className="text-slate-300">
            Showing {(page - 1) * pageSize + 1} -{' '}
            {Math.min(page * pageSize, sortedRows.length)} of {sortedRows.length}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="p-1.5 rounded-lg border border-white/10 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
            aria-label="Previous page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="font-mono text-slate-200 px-2">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            className="p-1.5 rounded-lg border border-white/10 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
            aria-label="Next page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
