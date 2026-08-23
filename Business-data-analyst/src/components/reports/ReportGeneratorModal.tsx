import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import { Modal } from '../common/Modal';
import { Sparkles, FileText, Check, Loader2 } from 'lucide-react';

interface ReportGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerated?: (reportId: string) => void;
}

export const ReportGeneratorModal: React.FC<ReportGeneratorModalProps> = ({
  isOpen,
  onClose,
  onGenerated
}) => {
  const { currentDataset, datasets, showToast } = useApp();
  const [selectedDatasetId, setSelectedDatasetId] = useState(currentDataset?.id || datasets[0]?.id || '');
  const [reportTitle, setReportTitle] = useState('');
  const [reportSubtitle, setReportSubtitle] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const [includeKpis, setIncludeKpis] = useState(true);
  const [includeCharts, setIncludeCharts] = useState(true);
  const [includeInsights, setIncludeInsights] = useState(true);
  const [includeRecommendations, setIncludeRecommendations] = useState(true);
  const [includeForecast, setIncludeForecast] = useState(true);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDatasetId) return;

    try {
      setIsGenerating(true);
      const chosenDs = datasets.find((d) => d.id === selectedDatasetId);
      const title = reportTitle.trim() || `${chosenDs?.name || 'Dataset'} Executive Intelligence Brief`;
      const subtitle = reportSubtitle.trim() || `Compiled with automated statistical profiling`;

      const newReport = await api.generateReport(selectedDatasetId, title, subtitle);
      showToast('success', 'Executive Report Generated', newReport.title);
      onGenerated?.(newReport.id);
      onClose();
    } catch (err: any) {
      showToast('error', 'Report generation failed', err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Generate Executive Intelligence Report"
      subtitle="Synthesize dynamic KPIs, statistical findings, recommendations, and forecast into a formal brief"
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 font-mono">
            Target Dataset Source
          </label>
          <select
            value={selectedDatasetId}
            onChange={(e) => setSelectedDatasetId(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            {datasets.map((ds) => (
              <option key={ds.id} value={ds.id} className="bg-slate-900 text-slate-200">
                {ds.name} ({ds.rowCount} rows, {ds.columnCount} cols)
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 font-mono">
            Report Title (Optional)
          </label>
          <input
            type="text"
            value={reportTitle}
            onChange={(e) => setReportTitle(e.target.value)}
            placeholder="e.g. Q3 Clinical Inpatient Operational Audit"
            className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 font-mono">
            Subtitle / Focus Memo
          </label>
          <input
            type="text"
            value={reportSubtitle}
            onChange={(e) => setReportSubtitle(e.target.value)}
            placeholder="e.g. Highlighting variance reduction and predictive risk factors"
            className="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="pt-2">
          <label className="block text-xs font-semibold text-slate-300 mb-2 font-mono">
            Included Intelligence Sections
          </label>
          <div className="space-y-2">
            {[
              { label: 'Executive KPI Cards & Sparklines', state: includeKpis, setter: setIncludeKpis },
              { label: 'Dynamic Visual Trajectories & Density Charts', state: includeCharts, setter: setIncludeCharts },
              { label: 'Statistical Finding Cards & Anomaly Alerts', state: includeInsights, setter: setIncludeInsights },
              { label: 'Strategic Action Recommendations & Impact', state: includeRecommendations, setter: setIncludeRecommendations },
              { label: 'Holt-Winters Predictive Horizon & Key Drivers', state: includeForecast, setter: setIncludeForecast }
            ].map((sec, idx) => (
              <label
                key={idx}
                className="flex items-center gap-2.5 p-2.5 rounded-xl bg-white/[0.03] border border-white/5 text-xs text-slate-300 cursor-pointer hover:bg-white/[0.06] transition-colors"
              >
                <input
                  type="checkbox"
                  checked={sec.state}
                  onChange={(e) => sec.setter(e.target.checked)}
                  className="rounded border-white/20 text-indigo-600 focus:ring-indigo-500 bg-white/5"
                />
                <span>{sec.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="pt-4 border-t border-white/10 flex items-center justify-end gap-2.5">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 rounded-xl text-xs font-semibold transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isGenerating}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 cursor-pointer"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Synthesizing Document...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Generate Executive Report</span>
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};
