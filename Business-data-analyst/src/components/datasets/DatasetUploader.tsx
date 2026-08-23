import React, { useState, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import { SAMPLE_DATASETS } from '../../utils/sampleData';
import {
  UploadCloud,
  FileText,
  Code2,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Database,
  ArrowRight,
  Loader2,
  Trash2,
  Plus,
  Layers,
  FolderKanban,
  Check,
  X,
  ChevronRight
} from 'lucide-react';

interface DatasetUploaderProps {
  onSuccess?: (datasetId: string) => void;
}

interface QueuedFile {
  id: string;
  file?: File;
  name: string;
  fileName: string;
  sizeBytes: number;
  fileType: 'csv' | 'json';
  content?: string;
  projectId?: string;
  status: 'pending' | 'processing' | 'success' | 'error';
  uploadProgress?: number;
  errorMessage?: string;
  resultDatasetId?: string;
  resultRowCount?: number;
  resultColCount?: number;
}

export const DatasetUploader: React.FC<DatasetUploaderProps> = ({ onSuccess }) => {
  const { refreshDatasets, setCurrentDatasetById, setCurrentRoute, showToast, projects, currentProject } = useApp();
  const [tab, setTab] = useState<'upload' | 'paste' | 'samples'>('upload');
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [queue, setQueue] = useState<QueuedFile[]>([]);
  const [currentProcessingIndex, setCurrentProcessingIndex] = useState<number>(-1);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Paste Tab State
  const [pasteName, setPasteName] = useState('');
  const [pasteContent, setPasteContent] = useState('');
  const [pasteProjectId, setPasteProjectId] = useState<string>(currentProject?.id || projects[0]?.id || '');

  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const handleFilesAdded = async (filesList: FileList | File[]) => {
    setErrorMsg(null);
    const filesArray = Array.from(filesList);
    if (filesArray.length === 0) return;

    const newQueued: QueuedFile[] = [];

    for (const file of filesArray) {
      const isJson = file.name.toLowerCase().endsWith('.json');
      const fileType: 'csv' | 'json' = isJson ? 'json' : 'csv';
      const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ');
      // Capitalize title
      const formattedTitle = nameWithoutExt
        .split(' ')
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' ');

      newQueued.push({
        id: `q-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        file,
        name: formattedTitle || file.name,
        fileName: file.name,
        sizeBytes: file.size,
        fileType,
        projectId: currentProject?.id || projects[0]?.id,
        status: 'pending'
      });
    }

    setQueue((prev) => [...prev, ...newQueued]);
    showToast('info', 'Files Staged in Queue', `Added ${newQueued.length} dataset(s) for ingestion.`);
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesAdded(e.dataTransfer.files);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFilesAdded(e.target.files);
    }
    // reset input value so re-uploading same file works
    if (e.target) e.target.value = '';
  };

  const removeQueueItem = (id: string) => {
    setQueue((prev) => prev.filter((item) => item.id !== id));
  };

  const updateQueueName = (id: string, newName: string) => {
    setQueue((prev) =>
      prev.map((item) => (item.id === id ? { ...item, name: newName } : item))
    );
  };

  const updateQueueProject = (id: string, projId: string) => {
    setQueue((prev) =>
      prev.map((item) => (item.id === id ? { ...item, projectId: projId } : item))
    );
  };

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve((e.target?.result as string) || '');
      reader.onerror = (e) => reject(new Error('Failed to read file.'));
      reader.readAsText(file);
    });
  };

  // Process all queued files sequentially
  const processBatchQueue = async (customQueue?: QueuedFile[]) => {
    const activeQueue = customQueue || queue;
    const pendingItems = activeQueue.filter((item) => item.status === 'pending' || item.status === 'error');
    if (pendingItems.length === 0) {
      showToast('info', 'All Datasets Processed', 'No pending files in the upload queue.');
      return;
    }

    setIsProcessing(true);
    setErrorMsg(null);
    let successCount = 0;
    let lastSuccessId = '';

    for (let i = 0; i < activeQueue.length; i++) {
      const item = activeQueue[i];
      if (item.status === 'success') continue;

      setCurrentProcessingIndex(i);
      setQueue((prev) =>
        prev.map((q, idx) => (idx === i ? { ...q, status: 'processing', errorMessage: undefined } : q))
      );

      try {
        let content = item.content;
        if (!content && item.file) {
          content = await readFileContent(item.file);
        }

        if (!content || !content.trim()) {
          throw new Error('File content is empty.');
        }

        let parsed;
        if (item.file) {
          parsed = await api.uploadFile(
            item.file,
            item.projectId,
            item.name.trim() || item.fileName,
            (percent) => {
              setQueue((prev) =>
                prev.map((q, idx) => (idx === i ? { ...q, uploadProgress: percent } : q))
              );
            }
          );
        } else {
          parsed = await api.parseRawDataset(
            content!,
            item.name.trim() || item.fileName,
            item.fileType,
            item.projectId,
            (percent) => {
              setQueue((prev) =>
                prev.map((q, idx) => (idx === i ? { ...q, uploadProgress: percent } : q))
              );
            }
          );
        }

        lastSuccessId = parsed.id;
        successCount++;

        setQueue((prev) =>
          prev.map((q, idx) =>
            idx === i
              ? {
                  ...q,
                  status: 'success',
                  resultDatasetId: parsed.id,
                  resultRowCount: parsed.rowCount,
                  resultColCount: parsed.columnCount
                }
              : q
          )
        );
      } catch (err: any) {
        setQueue((prev) =>
          prev.map((q, idx) =>
            idx === i
              ? {
                  ...q,
                  status: 'error',
                  errorMessage: err.message || 'Parsing error'
                }
              : q
          )
        );
      }
    }

    await refreshDatasets();
    setIsProcessing(false);
    setCurrentProcessingIndex(-1);

    if (successCount > 0 && lastSuccessId) {
      await setCurrentDatasetById(lastSuccessId);
      showToast(
        'success',
        'Batch Ingestion Complete',
        `Successfully ingested and profiled ${successCount} dataset(s).`
      );
    }
  };

  const handleExploreDataset = async (datasetId: string, targetView: 'analytics' | 'datasets' | 'chat' | 'forecast' = 'analytics') => {
    try {
      await setCurrentDatasetById(datasetId);
      setCurrentRoute(`/${targetView}`, datasetId);
    } catch (err: any) {
      showToast('error', 'Navigation failed', err.message);
    }
  };

  // Handle single paste
  const handlePasteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pasteContent.trim()) {
      setErrorMsg('Please paste valid CSV or JSON text.');
      return;
    }
    setErrorMsg(null);
    const isJson = pasteContent.trim().startsWith('{') || pasteContent.trim().startsWith('[');
    const fileType = isJson ? 'json' : 'csv';

    try {
      setIsProcessing(true);
      const parsed = await api.parseRawDataset(
        pasteContent,
        pasteName.trim() || 'Raw Pasted Dataset',
        fileType,
        pasteProjectId
      );
      await refreshDatasets();
      await setCurrentDatasetById(parsed.id);
      showToast('success', 'Dataset Ingested & Profiled', `${parsed.name} (${parsed.rowCount} rows)`);
      if (onSuccess) onSuccess(parsed.id);
      else setCurrentRoute('/analytics', parsed.id);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to parse raw content.');
      showToast('error', 'Ingestion failed', err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleLoadSample = async (sampleId: string) => {
    try {
      setIsProcessing(true);
      await setCurrentDatasetById(sampleId);
      const sample = SAMPLE_DATASETS.find((s) => s.id === sampleId);
      showToast('success', 'Sample Dataset Activated', sample?.name);
      if (onSuccess) onSuccess(sampleId);
      else setCurrentRoute('/analytics', sampleId);
    } catch (err: any) {
      showToast('error', 'Failed to load sample', err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const pendingCount = queue.filter((i) => i.status === 'pending' || i.status === 'error').length;
  const completedCount = queue.filter((i) => i.status === 'success').length;

  return (
    <div className="rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-2xl shadow-black/30 overflow-hidden space-y-0">
      {/* Header Navigation Tabs */}
      <div className="p-5 sm:p-6 border-b border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-white font-display">Dataset Schema Ingestion</h3>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Multi-Dataset Support
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Ingest multiple CSV or JSON datasets simultaneously with automatic column type inference and statistical profiling.
          </p>
        </div>

        <div className="flex items-center gap-1 bg-white/5 p-1 rounded-2xl border border-white/10">
          <button
            onClick={() => setTab('upload')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer ${
              tab === 'upload'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Multi-File Upload</span>
            {queue.length > 0 && (
              <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-white/20 text-white font-mono">
                {queue.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setTab('paste')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer ${
              tab === 'paste'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Paste Raw Data</span>
          </button>
          <button
            onClick={() => setTab('samples')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer ${
              tab === 'samples'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Sample Datasets</span>
          </button>
        </div>
      </div>

      <div className="p-6">
        {errorMsg && (
          <div className="mb-5 p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* TAB 1: Multi-File Dropzone & Staging Queue */}
        {tab === 'upload' && (
          <div className="space-y-6">
            {/* Dropzone area */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleFileDrop}
              className={`p-8 sm:p-10 border-2 border-dashed rounded-3xl flex flex-col items-center justify-center text-center transition-all ${
                isDragging
                  ? 'border-indigo-500 bg-indigo-500/10 scale-[0.99]'
                  : 'border-white/15 hover:border-white/30 bg-white/[0.02]'
              }`}
            >
              <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-3 shadow-lg shadow-indigo-500/10">
                {isProcessing ? (
                  <Loader2 className="w-7 h-7 animate-spin" />
                ) : (
                  <UploadCloud className="w-7 h-7" />
                )}
              </div>

              <h4 className="text-sm font-semibold text-white font-display">
                Drag and drop single or multiple datasets here
              </h4>
              <p className="text-xs text-slate-400 max-w-md mt-1 leading-relaxed">
                Select multiple <span className="font-mono text-indigo-300">.csv</span>,{' '}
                <span className="font-mono text-indigo-300">.json</span>, or{' '}
                <span className="font-mono text-indigo-300">.tsv</span> files. You can queue and profile all schemas at once.
              </p>

              <div className="mt-5 flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition-all cursor-pointer"
                >
                  <Plus className="w-4 h-4" />
                  <span>Select Multiple Files</span>
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".csv,.json,.tsv,.txt,text/csv,application/json,text/plain"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            </div>

            {/* STAGING QUEUE */}
            {queue.length > 0 && (
              <div className="space-y-4 pt-2">
                {/* Staging Queue Header */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-white/10">
                  <div className="flex items-center gap-2.5">
                    <Layers className="w-4 h-4 text-indigo-400" />
                    <h4 className="text-sm font-bold text-white font-display">
                      Staging Queue ({queue.length} Datasets)
                    </h4>
                    {completedCount > 0 && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        {completedCount} Ingested
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setQueue([])}
                      disabled={isProcessing}
                      className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                    >
                      Clear Queue
                    </button>
                    <button
                      onClick={() => processBatchQueue()}
                      disabled={isProcessing || pendingCount === 0}
                      className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-sky-600 hover:from-indigo-500 hover:to-sky-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 cursor-pointer"
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Profiling {currentProcessingIndex + 1} of {queue.length}...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>Ingest & Profile All ({pendingCount})</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Staged pending guide alert */}
                {pendingCount > 0 && !isProcessing && (
                  <div className="p-3.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <Sparkles className="w-4 h-4 text-indigo-400 shrink-0" />
                      <p className="text-xs text-indigo-200">
                        <span className="font-semibold text-white">{pendingCount} dataset(s) staged in queue.</span> Click below to start automated statistical profiling and AI analysis.
                      </p>
                    </div>
                    <button
                      onClick={() => processBatchQueue()}
                      className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shrink-0 shadow-md shadow-indigo-600/30 cursor-pointer transition-all flex items-center gap-1.5"
                    >
                      <span>Ingest Now</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                {/* Batch completed banner */}
                {completedCount > 0 && pendingCount === 0 && !isProcessing && (
                  <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                      <div>
                        <p className="text-xs font-bold text-white">
                          All {completedCount} datasets ingested and analyzed successfully!
                        </p>
                        <p className="text-[11px] text-emerald-200/80">
                          Ready for visual charts, statistical correlation, and AI chat.
                        </p>
                      </div>
                    </div>
                    {queue.find((q) => q.status === 'success')?.resultDatasetId && (
                      <button
                        onClick={() => {
                          const firstSuccess = queue.find((q) => q.status === 'success')?.resultDatasetId;
                          if (firstSuccess) handleExploreDataset(firstSuccess, 'analytics');
                        }}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/25 transition-all flex items-center gap-1.5 cursor-pointer shrink-0"
                      >
                        <span>Open Analytics Dashboard</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                )}

                {/* Progress bar during batch processing */}
                {isProcessing && (
                  <div className="space-y-1.5 p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-indigo-300 font-medium">Batch Ingestion Progress</span>
                      <span className="text-indigo-200 font-mono text-[11px]">
                        {currentProcessingIndex + 1} / {queue.length}
                      </span>
                    </div>
                    <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-sky-400 transition-all duration-300"
                        style={{
                          width: `${((currentProcessingIndex + 1) / queue.length) * 100}%`
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* List of Queued Datasets */}
                <div className="space-y-3">
                  {queue.map((item, idx) => (
                    <div
                      key={item.id}
                      className={`p-4 rounded-2xl backdrop-blur-md border transition-all ${
                        item.status === 'processing'
                          ? 'bg-indigo-600/10 border-indigo-500/40 ring-1 ring-indigo-500/20'
                          : item.status === 'success'
                          ? 'bg-emerald-500/5 border-emerald-500/20'
                          : item.status === 'error'
                          ? 'bg-rose-500/5 border-rose-500/20'
                          : 'bg-white/[0.03] border-white/10 hover:border-white/20'
                      }`}
                    >
                      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                        {/* File details & Name input */}
                        <div className="flex items-start gap-3 flex-1 min-w-0">
                          <div
                            className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${
                              item.status === 'success'
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                : item.status === 'processing'
                                ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                                : 'bg-white/5 text-slate-400 border border-white/10'
                            }`}
                          >
                            {item.status === 'processing' ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : item.status === 'success' ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            ) : (
                              <FileText className="w-4 h-4" />
                            )}
                          </div>

                          <div className="space-y-1.5 flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <input
                                type="text"
                                value={item.name}
                                disabled={item.status === 'processing' || item.status === 'success'}
                                onChange={(e) => updateQueueName(item.id, e.target.value)}
                                placeholder="Dataset Display Name"
                                className="px-2.5 py-1 bg-white/5 border border-white/10 rounded-lg text-xs font-semibold text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 max-w-xs"
                              />
                              <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-mono font-bold bg-white/10 text-slate-300 border border-white/10">
                                {item.fileType}
                              </span>
                              <span className="text-[11px] text-slate-400 font-mono">
                                {formatFileSize(item.sizeBytes)}
                              </span>
                            </div>

                            <p className="text-[11px] text-slate-400 truncate">
                              Original file: <span className="font-mono text-slate-300">{item.fileName}</span>
                            </p>

                            {item.status === 'processing' && (
                              <div className="space-y-1 mt-1">
                                <div className="flex items-center justify-between text-[10px] text-indigo-300 font-mono">
                                  <span>{item.uploadProgress !== undefined && item.uploadProgress < 100 ? 'Uploading to backend...' : 'Profiling schema & computing KPIs...'}</span>
                                  <span>{item.uploadProgress !== undefined ? `${item.uploadProgress}%` : ''}</span>
                                </div>
                                <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-indigo-500 transition-all duration-200"
                                    style={{ width: `${item.uploadProgress ?? 65}%` }}
                                  />
                                </div>
                              </div>
                            )}

                            {item.status === 'error' && (
                              <p className="text-[11px] text-rose-300 font-medium">
                                {item.errorMessage}
                              </p>
                            )}

                            {item.status === 'success' && (
                              <div className="flex items-center gap-2 text-[11px] text-emerald-300 font-mono">
                                <span>{item.resultRowCount} rows</span>
                                <span>•</span>
                                <span>{item.resultColCount} columns profiled</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Project selector & Action button */}
                        <div className="flex items-center gap-2 self-end md:self-center flex-wrap">
                          {item.status !== 'success' && (
                            <div className="flex items-center gap-1.5">
                              <FolderKanban className="w-3.5 h-3.5 text-slate-500" />
                              <select
                                value={item.projectId || ''}
                                onChange={(e) => updateQueueProject(item.id, e.target.value)}
                                disabled={item.status === 'processing'}
                                className="px-2.5 py-1.5 bg-white/5 border border-white/10 rounded-xl text-[11px] text-slate-300 focus:outline-none focus:border-indigo-500 cursor-pointer max-w-[150px]"
                              >
                                {projects.map((p) => (
                                  <option key={p.id} value={p.id}>
                                    {p.name}
                                  </option>
                                ))}
                              </select>
                            </div>
                          )}

                          {item.status === 'success' && item.resultDatasetId ? (
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <button
                                onClick={() => handleExploreDataset(item.resultDatasetId!, 'analytics')}
                                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-600/25 transition-all flex items-center gap-1.5 cursor-pointer"
                              >
                                <Sparkles className="w-3.5 h-3.5" />
                                <span>Deep Analytics</span>
                              </button>
                              <button
                                onClick={() => handleExploreDataset(item.resultDatasetId!, 'datasets')}
                                className="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-slate-200 border border-white/10 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1 cursor-pointer"
                              >
                                <span>View Data</span>
                              </button>
                              <button
                                onClick={() => handleExploreDataset(item.resultDatasetId!, 'chat')}
                                className="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-slate-200 border border-white/10 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1 cursor-pointer"
                              >
                                <span>AI Chat</span>
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => removeQueueItem(item.id)}
                              disabled={item.status === 'processing'}
                              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-colors cursor-pointer"
                              title="Remove from queue"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Paste Raw Data */}
        {tab === 'paste' && (
          <form onSubmit={handlePasteSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 font-mono">
                  Dataset Name
                </label>
                <input
                  type="text"
                  value={pasteName}
                  onChange={(e) => setPasteName(e.target.value)}
                  placeholder="e.g. Real-Time Telemetry Log"
                  className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 font-mono">
                  Target Project Container
                </label>
                <select
                  value={pasteProjectId}
                  onChange={(e) => setPasteProjectId(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 font-mono">
                Paste Raw CSV or JSON Text
              </label>
              <textarea
                rows={8}
                value={pasteContent}
                onChange={(e) => setPasteContent(e.target.value)}
                placeholder={`sensor_id,timestamp,temperature_c,vibration_hz,operational_status\nSN-101,2026-08-01T08:00:00Z,68.4,12.2,nominal\nSN-102,2026-08-01T08:00:00Z,71.2,14.8,warning\nSN-103,2026-08-01T08:00:00Z,64.1,11.0,nominal`}
                className="w-full p-3.5 bg-white/5 border border-white/10 rounded-2xl text-xs font-mono text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <button
              type="submit"
              disabled={isProcessing || !pasteContent.trim()}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Profiling Schema & Statistics...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Parse & Ingest Dataset</span>
                </>
              )}
            </button>
          </form>
        )}

        {/* TAB 3: Diverse Sample Datasets */}
        {tab === 'samples' && (
          <div>
            <div className="mb-4">
              <p className="text-xs text-slate-400">
                Load rich sample datasets across non-sales domains to test schema-agnostic intelligence and dynamic analytics:
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {SAMPLE_DATASETS.map((sample) => (
                <div
                  key={sample.id}
                  className="p-4 rounded-2xl backdrop-blur-md bg-white/[0.03] border border-white/10 hover:border-white/25 hover:bg-white/[0.06] transition-all flex flex-col justify-between group"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="text-[10px] font-semibold px-2 py-0.5 bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 rounded-full font-mono">
                        {sample.domain}
                      </span>
                      <span className="text-[10px] font-mono text-slate-400">
                        {sample.columnCount} cols
                      </span>
                    </div>
                    <h5 className="text-xs font-bold text-white font-display group-hover:text-indigo-300 transition-colors">
                      {sample.name}
                    </h5>
                    <p className="text-[11px] text-slate-300 mt-1 line-clamp-2 leading-relaxed">
                      {sample.description}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between">
                    <span className="text-[10px] text-slate-400 font-mono">
                      {sample.rowCount} observations
                    </span>
                    <button
                      onClick={() => handleLoadSample(sample.id)}
                      disabled={isProcessing}
                      className="px-2.5 py-1 bg-white/5 hover:bg-indigo-600 hover:text-white text-indigo-300 border border-white/10 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all cursor-pointer"
                    >
                      <span>Load</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
