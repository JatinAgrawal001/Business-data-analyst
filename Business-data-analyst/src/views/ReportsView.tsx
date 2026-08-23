import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { ReportCard } from '../components/reports/ReportCard';
import { ReportGeneratorModal } from '../components/reports/ReportGeneratorModal';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import { Modal } from '../components/common/Modal';
import { FileText, Plus, Download, Calendar, User, Sparkles, Share2 } from 'lucide-react';
import { Report } from '../types';
import { api } from '../services/api';

export const ReportsView: React.FC = () => {
  const { reports, refreshReports, showToast, isLoading } = useApp();
  const [isGeneratorOpen, setIsGeneratorOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  const reportList = reports || [];

  if (isLoading && reportList.length === 0) {
    return <LoadingState message="Fetching compiled executive reports..." />;
  }

  const handleDeleteReport = (id: string) => {
    showToast('info', 'Report Archived', 'Report removed from active list.');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold font-display text-white flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-indigo-400" />
            <span>Executive Reports & Intelligence Briefs</span>
          </h2>
          <p className="text-xs text-slate-300 mt-1">
            Automated synthesized documents summarizing statistical distributions, strategic actions, and predictive horizon trajectories
          </p>
        </div>

        <button
          onClick={() => setIsGeneratorOpen(true)}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 cursor-pointer shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Generate New Report</span>
        </button>
      </div>

      {/* Reports Grid */}
      {reportList.length === 0 ? (
        <EmptyState
          title="No Published Reports"
          description="Synthesize your first executive intelligence brief using the automated reporting engine."
          actionLabel="Generate Report"
          onAction={() => setIsGeneratorOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {reportList.map((report) => (
            <div
              key={report.id}
              onClick={() => setSelectedReport(report)}
              className="cursor-pointer"
            >
              <ReportCard
                report={report}
                onView={() => setSelectedReport(report)}
                onDelete={() => handleDeleteReport(report.id)}
              />
            </div>
          ))}
        </div>
      )}

      {/* Generator Modal */}
      <ReportGeneratorModal
        isOpen={isGeneratorOpen}
        onClose={() => setIsGeneratorOpen(false)}
        onGenerated={async (id) => {
          await refreshReports();
          const rep = reports.find((r) => r.id === id);
          if (rep) setSelectedReport(rep);
        }}
      />

      {/* View / Read Report Modal */}
      {selectedReport && (
        <Modal
          isOpen={!!selectedReport}
          onClose={() => setSelectedReport(null)}
          title={selectedReport.title}
          subtitle={selectedReport.subtitle}
          maxWidth="2xl"
        >
          <div className="space-y-6 text-xs text-slate-200">
            {/* Metadata Bar */}
            <div className="p-4 rounded-xl bg-white/[0.03] border border-white/10 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1.5 text-slate-400">
                  <Calendar className="w-3.5 h-3.5" />
                  {new Date(selectedReport.generatedAt).toLocaleDateString()}
                </span>
                <span className="flex items-center gap-1.5 text-slate-400">
                  <User className="w-3.5 h-3.5" />
                  {selectedReport.author}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  {selectedReport.cadence}
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {selectedReport.status}
                </span>
              </div>
            </div>

            {/* Executive Summary */}
            <div className="space-y-2">
              <h4 className="text-sm font-bold font-display text-white">Executive Summary</h4>
              <p className="leading-relaxed text-slate-300 bg-white/[0.02] p-4 rounded-xl border border-white/5">
                {selectedReport.executiveSummary}
              </p>
            </div>

            {/* Sections */}
            <div className="space-y-4">
              <h4 className="text-sm font-bold font-display text-white">Report Sections</h4>
              {selectedReport.sections.map((sec, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-white/[0.03] border border-white/10 space-y-2">
                  <h5 className="font-semibold text-slate-100 flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-300 flex items-center justify-center text-[10px] font-bold">
                      {idx + 1}
                    </span>
                    <span>{sec.title}</span>
                  </h5>
                  <p className="text-slate-300 leading-relaxed text-xs">
                    {typeof sec.content === 'string'
                      ? sec.content
                      : Array.isArray(sec.content)
                      ? `${sec.content.length} items synthesized and verified in this section.`
                      : typeof sec.content === 'object' && sec.content !== null
                      ? JSON.stringify(sec.content)
                      : String(sec.content || '')}
                  </p>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="pt-4 border-t border-white/10 flex items-center justify-end gap-3">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(window.location.href);
                  showToast('info', 'Report Link Copied to Clipboard');
                }}
                className="px-3 py-2 bg-white/5 hover:bg-white/10 text-slate-300 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                <Share2 className="w-3.5 h-3.5" />
                <span>Share</span>
              </button>
              <button
                onClick={async () => {
                  await api.downloadReportFile(selectedReport.id, 'html', selectedReport.title);
                  showToast('success', 'HTML Export Complete', `Downloaded ${selectedReport.title}.html`);
                }}
                className="px-3.5 py-2 bg-white/10 hover:bg-white/15 text-slate-200 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download HTML</span>
              </button>
              <button
                onClick={async () => {
                  await api.downloadReportFile(selectedReport.id, 'pdf', selectedReport.title);
                  showToast('success', 'PDF Export Complete', `Downloaded ${selectedReport.title}.pdf`);
                }}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-600/30 transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download PDF</span>
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
