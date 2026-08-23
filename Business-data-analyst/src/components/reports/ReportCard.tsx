import React from 'react';
import { Report } from '../../types';
import { FileText, Download, Calendar, User, Trash2, ArrowUpRight, Share2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';

interface ReportCardProps {
  report: Report;
  onView?: () => void;
  onDelete?: () => void;
}

export const ReportCard: React.FC<ReportCardProps> = ({ report, onView, onDelete }) => {
  const { showToast } = useApp();

  const handleDownload = () => {
    showToast('success', 'Report Export Started', `Downloading ${report.title} (${report.format.toUpperCase()})`);
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    showToast('info', 'Report Link Copied to Clipboard');
  };

  return (
    <div className="p-6 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 hover:border-white/25 hover:bg-white/[0.06] transition-all duration-200 shadow-xl shadow-black/20 flex flex-col justify-between group">
      <div>
        {/* Top Badges */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-white/5 text-slate-300 border border-white/10 font-mono">
              {report.cadence || 'On Demand'}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
              {report.status}
            </span>
          </div>
        </div>

        {/* Title & Description */}
        <h4 className="text-base font-bold text-white font-display group-hover:text-indigo-300 transition-colors">
          {report.title}
        </h4>
        {report.subtitle && (
          <p className="text-xs text-slate-400 mt-1 font-medium">{report.subtitle}</p>
        )}
        <p className="text-xs text-slate-300 mt-2 leading-relaxed line-clamp-3">
          {report.executiveSummary}
        </p>

        {/* Sections Pill tags */}
        <div className="flex flex-wrap gap-1.5 mt-4">
          {report.sections.map((sec) => (
            <span
              key={sec.id}
              className="text-[10px] px-2 py-0.5 bg-white/5 border border-white/10 text-slate-300 rounded-md font-mono"
            >
              {sec.title}
            </span>
          ))}
        </div>
      </div>

      {/* Footer Info & Actions */}
      <div className="mt-5 pt-3.5 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            {new Date(report.generatedAt).toLocaleDateString()}
          </span>
          <span className="flex items-center gap-1">
            <User className="w-3.5 h-3.5 text-slate-400" />
            {report.author}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleShare}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors cursor-pointer"
            title="Share Report"
          >
            <Share2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleDownload}
            className="p-1.5 text-slate-400 hover:text-indigo-300 hover:bg-white/10 rounded-lg transition-colors cursor-pointer"
            title="Download PDF"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
          {onDelete && (
            <button
              onClick={onDelete}
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-white/10 rounded-lg transition-colors cursor-pointer"
              title="Delete Report"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
