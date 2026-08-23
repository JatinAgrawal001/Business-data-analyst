import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { DatasetPreview } from '../components/datasets/DatasetPreview';
import { DataTable } from '../components/tables/DataTable';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import { Modal } from '../components/common/Modal';
import { Dataset } from '../types';
import {
  FileSpreadsheet,
  BarChart3,
  Layers,
  Database,
  Trash2,
  Plus,
  CheckCircle2,
  Calendar,
  Eye,
  AlertTriangle,
  FileCode
} from 'lucide-react';
import { formatNumber } from '../utils/dataEngine';

export const DatasetDetailView: React.FC = () => {
  const {
    currentDataset,
    datasets,
    setCurrentDatasetById,
    deleteDataset,
    setCurrentRoute,
    refreshDatasets,
    showToast,
    isLoading
  } = useApp();

  const [activeTab, setActiveTab] = useState<'schema' | 'rows' | 'all'>('schema');
  const [inspectedRow, setInspectedRow] = useState<Record<string, any> | null>(null);
  const [datasetToDelete, setDatasetToDelete] = useState<Dataset | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  if (isLoading && !currentDataset && datasets.length === 0) {
    return <LoadingState message="Loading dataset repository and schemas..." />;
  }

  if (datasets.length === 0) {
    return (
      <EmptyState
        title="No Datasets In Workspace"
        description="You have not uploaded any datasets yet. Ingest your first CSV or JSON file to start autonomous statistical profiling and AI analysis."
        actionLabel="Upload Dataset"
        onAction={() => setCurrentRoute('/datasets/upload')}
      />
    );
  }

  const handleDeleteConfirm = async () => {
    if (!datasetToDelete) return;
    try {
      setIsDeleting(true);
      await deleteDataset(datasetToDelete.id);
      setDatasetToDelete(null);
      showToast('info', 'Dataset deleted');
    } catch {
      showToast('error', 'Failed to delete dataset');
    } finally {
      setIsDeleting(false);
    }
  };

  const targetDataset = currentDataset || datasets[0];

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Header & Overview */}
      <div className="p-6 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-xl flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-2 flex-wrap">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider font-mono">
              {datasets.length} {datasets.length === 1 ? 'Dataset Loaded' : 'Datasets Ingested'}
            </span>
            {targetDataset && (
              <span className="text-xs text-slate-400 font-mono flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                Active: <strong className="text-slate-200">{targetDataset.name}</strong>
              </span>
            )}
          </div>
          <h2 className="text-2xl font-bold font-display text-white flex items-center gap-2.5">
            <Database className="w-6 h-6 text-indigo-400" />
            <span>Dataset Repository & Schema Explorer</span>
          </h2>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
            Browse all uploaded tabular data assets, inspect statistical schemas, and explore distribution profiles.
          </p>
        </div>

        {/* Global Action Shortcuts */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setCurrentRoute('/datasets/upload')}
            className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-sky-600 hover:from-indigo-500 hover:to-sky-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-1.5 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Upload New Dataset</span>
          </button>
          {targetDataset && (
            <button
              onClick={() => setCurrentRoute('/analytics', targetDataset.id)}
              className="px-4 py-2 bg-white/5 hover:bg-white/10 text-slate-200 border border-white/10 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer backdrop-blur-md"
            >
              <BarChart3 className="w-3.5 h-3.5 text-indigo-400" />
              <span>Deep Analytics</span>
            </button>
          )}
        </div>
      </div>

      {/* ALL UPLOADED DATASETS REPOSITORY CARDS */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-sm font-bold text-slate-200 font-display flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span>All Uploaded Datasets ({datasets.length})</span>
          </h3>
          <span className="text-xs text-slate-400">
            Click any dataset to set as active schema
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {datasets.map((ds) => {
            const isSelected = ds.id === targetDataset?.id;
            return (
              <div
                key={ds.id}
                className={`p-5 rounded-3xl backdrop-blur-xl transition-all flex flex-col justify-between relative group shadow-xl ${
                  isSelected
                    ? 'bg-gradient-to-br from-indigo-950/50 via-slate-900/80 to-slate-950/90 border-2 border-indigo-500 shadow-indigo-500/10'
                    : 'bg-white/[0.04] border border-white/10 hover:border-white/20 hover:bg-white/[0.06]'
                }`}
              >
                <div>
                  {/* Top Bar with Badges and Delete button */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-white/10 text-slate-300 border border-white/10 uppercase font-mono">
                        {ds.fileType?.toUpperCase() || 'CSV'}
                      </span>
                      {isSelected && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                          <CheckCircle2 className="w-3 h-3 text-indigo-400" />
                          <span>Active</span>
                        </span>
                      )}
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono">
                        <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
                        <span>Ready</span>
                      </span>
                    </div>

                    {/* Delete action button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setDatasetToDelete(ds);
                      }}
                      className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-colors cursor-pointer"
                      title="Delete this dataset"
                      aria-label={`Delete ${ds.name}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Dataset Title & Description */}
                  <h4 className="text-base font-bold text-white font-display group-hover:text-indigo-300 transition-colors line-clamp-1">
                    {ds.name}
                  </h4>
                  <p className="text-xs text-slate-300 mt-1 leading-relaxed line-clamp-2">
                    {ds.description || 'Uploaded dataset ready for statistical profiling & analysis.'}
                  </p>

                  {/* Key Metrics Chips */}
                  <div className="grid grid-cols-2 gap-2 mt-4 p-2.5 rounded-2xl bg-black/30 border border-white/5 text-xs font-mono">
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase block">Observations</span>
                      <span className="text-xs font-bold text-indigo-300 mt-0.5 block">
                        {formatNumber(ds.rowCount, 0)} rows
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase block">Dimensions</span>
                      <span className="text-xs font-bold text-emerald-300 mt-0.5 block">
                        {ds.columnCount} columns
                      </span>
                    </div>
                  </div>
                </div>

                {/* Card Action Footer */}
                <div className="mt-5 pt-3.5 border-t border-white/10 flex items-center justify-between gap-2">
                  <span className="text-[10px] text-slate-400 font-mono">
                    {new Date(ds.uploadedAt).toLocaleDateString()}
                  </span>

                  <div className="flex items-center gap-1.5">
                    {!isSelected ? (
                      <button
                        onClick={() => setCurrentDatasetById(ds.id)}
                        className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-sm transition-all flex items-center gap-1 cursor-pointer"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Select</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => setCurrentRoute('/analytics', ds.id)}
                        className="px-3 py-1.5 bg-white/10 hover:bg-white/15 text-indigo-300 border border-indigo-500/30 rounded-xl text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer"
                      >
                        <BarChart3 className="w-3.5 h-3.5 text-indigo-400" />
                        <span>Analytics</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ACTIVE DATASET DEEP INSPECTION */}
      {targetDataset && (
        <div className="space-y-4 pt-2">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-bold text-white font-display flex items-center gap-2">
                <FileSpreadsheet className="w-5 h-5 text-indigo-400" />
                <span>Active Dataset: {targetDataset.name}</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Inspect column schemas, data types, standard variances, and raw observations.
              </p>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-1.5 bg-white/5 p-1 rounded-2xl border border-white/10">
              <button
                onClick={() => setActiveTab('schema')}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer ${
                  activeTab === 'schema'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/25'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <FileCode className="w-3.5 h-3.5" />
                <span>Schema & Stats</span>
              </button>
              <button
                onClick={() => setActiveTab('rows')}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer ${
                  activeTab === 'rows'
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/25'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Raw Records ({targetDataset.rowCount})</span>
              </button>
            </div>
          </div>

          {/* Active Tab Component */}
          {activeTab === 'schema' ? (
            <DatasetPreview dataset={targetDataset} />
          ) : (
            <DataTable
              dataset={targetDataset}
              onRowClick={(row) => setInspectedRow(row)}
            />
          )}
        </div>
      )}

      {/* DELETE CONFIRMATION MODAL */}
      {datasetToDelete && (
        <Modal
          isOpen={!!datasetToDelete}
          onClose={() => !isDeleting && setDatasetToDelete(null)}
          title="Delete Dataset"
          subtitle="Permanent dataset removal confirmation"
          maxWidth="sm"
        >
          <div className="space-y-4">
            <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-bold text-rose-200">
                  Are you sure you want to delete "{datasetToDelete.name}"?
                </p>
                <p className="text-[11px] text-rose-300/80 mt-1 leading-relaxed">
                  This will permanently delete this dataset ({datasetToDelete.rowCount} rows, {datasetToDelete.columnCount} columns), all computed statistical metrics, and stored files from local and cloud storage.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                onClick={() => setDatasetToDelete(null)}
                disabled={isDeleting}
                className="px-4 py-2 bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 rounded-xl text-xs font-semibold transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                disabled={isDeleting}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-lg shadow-rose-600/30 transition-all flex items-center gap-1.5 cursor-pointer"
              >
                {isDeleting ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Yes, Delete Dataset</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Row Inspection Modal */}
      {inspectedRow && (
        <Modal
          isOpen={!!inspectedRow}
          onClose={() => setInspectedRow(null)}
          title="Observation Record Inspector"
          subtitle="Detailed field key-value inspection"
          maxWidth="md"
        >
          <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
            {Object.entries(inspectedRow).map(([key, val]) => (
              <div
                key={key}
                className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between text-xs"
              >
                <span className="font-mono text-slate-400">{key}:</span>
                <span className="font-semibold text-slate-100 font-mono">
                  {val === null ? 'null' : typeof val === 'number' ? formatNumber(val, 2) : String(val)}
                </span>
              </div>
            ))}
          </div>
        </Modal>
      )}
    </div>
  );
};
