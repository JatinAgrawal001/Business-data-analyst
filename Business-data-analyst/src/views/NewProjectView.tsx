import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { ArrowLeft, FolderPlus, Sparkles, Building, Layers } from 'lucide-react';

export const NewProjectView: React.FC = () => {
  const { setCurrentRoute, refreshProjects, setCurrentProjectById, showToast } = useApp();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [domain, setDomain] = useState('Operations & Telemetry');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    try {
      setIsSubmitting(true);
      const newProj = await api.createProject({
        name: name.trim(),
        description: description.trim() || 'Custom business analytical workspace',
        datasetIds: [],
        status: 'active',
        tags: [domain, 'Workspace']
      });
      await refreshProjects();
      await setCurrentProjectById(newProj.id);
      showToast('success', 'Project Created', newProj.name);
      setCurrentRoute('/dashboard');
    } catch (err: any) {
      showToast('error', 'Creation failed', err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <button
        onClick={() => setCurrentRoute('/projects')}
        className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Projects</span>
      </button>

      <div className="p-8 rounded-3xl backdrop-blur-xl bg-white/[0.04] border border-white/10 shadow-2xl">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <FolderPlus className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold font-display text-white">
              Create Analytical Workspace
            </h2>
            <p className="text-xs text-slate-300 mt-0.5">
              Set up a dedicated project container for datasets and automated models
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Project Name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Telemetry Fleet Monitoring Q3"
              className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:bg-white/[0.07]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Business Domain / Vertical
            </label>
            <select
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="Healthcare & Clinical">Healthcare & Clinical</option>
              <option value="Supply Chain & Logistics">Supply Chain & Logistics</option>
              <option value="Renewable Energy & IoT">Renewable Energy & IoT</option>
              <option value="Higher Education & Learning">Higher Education & Learning</option>
              <option value="SaaS & Cloud Operations">SaaS & Cloud Operations</option>
              <option value="Manufacturing & Quality">Manufacturing & Quality</option>
              <option value="Custom General Analytics">Custom General Analytics</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Description & Objectives
            </label>
            <textarea
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Track anomaly frequencies, seasonal variance, and cross-variable correlations..."
              className="w-full p-4 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:bg-white/[0.07]"
            />
          </div>

          <div className="pt-4 border-t border-white/10 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => setCurrentRoute('/projects')}
              className="px-4 py-2.5 bg-white/5 hover:bg-white/10 text-slate-300 rounded-xl text-xs font-semibold transition-colors cursor-pointer border border-white/10"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !name.trim()}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isSubmitting ? 'Creating...' : 'Initialize Project'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
