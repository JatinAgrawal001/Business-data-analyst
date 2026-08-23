import React from 'react';
import { useApp } from '../context/AppContext';
import { Project } from '../types';
import {
  FolderKanban,
  Plus,
  Calendar,
  Database,
  ArrowRight,
  MoreVertical,
  Layers,
  Sparkles
} from 'lucide-react';

export const ProjectsView: React.FC = () => {
  const { projects, currentProject, setCurrentProjectById, setCurrentRoute, showToast } = useApp();

  const handleSelectProject = async (proj: Project) => {
    await setCurrentProjectById(proj.id);
    showToast('info', 'Project Activated', proj.name);
    setCurrentRoute('/dashboard');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold font-display text-slate-100 flex items-center gap-2">
            <FolderKanban className="w-6 h-6 text-indigo-400" />
            <span>Analytical Projects & Workspaces</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Group datasets, executive reports, and automated forecasting models by business domain
          </p>
        </div>

        <button
          onClick={() => setCurrentRoute('/projects/new')}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-600/25 transition-all flex items-center gap-2 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Project</span>
        </button>
      </div>

      {/* Projects Grid or Empty State */}
      {projects.length === 0 ? (
        <div className="p-12 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-dashed border-white/15 text-center flex flex-col items-center justify-center">
          <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
            <FolderKanban className="w-7 h-7" />
          </div>
          <h3 className="text-lg font-bold text-white font-display">No Projects Yet</h3>
          <p className="text-xs text-slate-400 max-w-md mt-2 leading-relaxed">
            Create your first analytical workspace to organize your datasets, automated insights, and executive reports.
          </p>
          <button
            onClick={() => setCurrentRoute('/projects/new')}
            className="mt-6 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/25 transition-all flex items-center gap-2 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Create First Project</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {projects.map((proj) => {
            const isActive = currentProject?.id === proj.id;
            return (
              <div
                key={proj.id}
                onClick={() => handleSelectProject(proj)}
                className={`p-6 rounded-3xl backdrop-blur-xl bg-white/[0.04] border transition-all cursor-pointer flex flex-col justify-between group shadow-xl shadow-black/20 ${
                  isActive
                    ? 'border-indigo-500/80 shadow-indigo-500/10 bg-white/[0.07]'
                    : 'border-white/10 hover:border-white/25 hover:bg-white/[0.06]'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 uppercase tracking-wider font-mono">
                      {proj.tags?.[0] || 'Workspace'}
                    </span>
                    {isActive && (
                      <span className="text-[10px] font-bold px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">
                        Active Workspace
                      </span>
                    )}
                  </div>

                  <h3 className="text-base font-bold text-white font-display group-hover:text-indigo-300 transition-colors">
                    {proj.name}
                  </h3>
                  <p className="text-xs text-slate-300 mt-1.5 leading-relaxed line-clamp-2">
                    {proj.description}
                  </p>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-2 mt-5 p-3 rounded-2xl bg-white/[0.03] border border-white/5 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase block font-mono">Datasets</span>
                      <span className="text-sm font-bold font-mono text-white mt-0.5 block">
                        {proj.datasetIds?.length || 0} Attached
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase block font-mono">Status</span>
                      <span className="text-sm font-bold font-mono text-emerald-400 mt-0.5 block capitalize">
                        {proj.status}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Footer */}
                <div className="mt-5 pt-3.5 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-1 text-[11px]">
                    <Calendar className="w-3.5 h-3.5 text-slate-500" />
                    {new Date(proj.updatedAt).toLocaleDateString()}
                  </span>
                  <span className="text-xs font-semibold text-indigo-400 group-hover:text-indigo-300 flex items-center gap-1 transition-colors">
                    <span>Open Workspace</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
