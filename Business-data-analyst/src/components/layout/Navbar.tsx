import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import {
  Search,
  Database,
  Sparkles,
  Bell,
  Upload,
  Plus,
  ChevronDown,
  User,
  Settings,
  LogOut,
  FolderKanban,
  Check
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const {
    user,
    datasets,
    currentDataset,
    currentProject,
    setCurrentDatasetById,
    setCurrentRoute,
    currentRoute,
    logout,
    showToast
  } = useApp();

  const [showDatasetMenu, setShowDatasetMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    showToast('info', 'Searching Dataset Dimensions', `Filtered insights for "${searchQuery}"`);
    setCurrentRoute('/analytics', currentDataset?.id);
  };

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 sm:px-6 backdrop-blur-xl bg-[#0A0B10]/75 border-b border-white/10">
      {/* Left section: Breadcrumb & Dataset Quick Selector */}
      <div className="flex items-center gap-3 min-w-0">
        <div className="hidden md:flex items-center gap-2 text-xs text-slate-400">
          <FolderKanban className="w-3.5 h-3.5 text-indigo-400" />
          <span className="font-medium text-slate-300 truncate max-w-[140px]">
            {currentProject?.name || 'Workspace'}
          </span>
          <span className="text-slate-600">/</span>
        </div>

        {/* Dataset Quick Switcher dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowDatasetMenu(!showDatasetMenu)}
            className="flex items-center gap-2 px-3 py-1.5 backdrop-blur-md bg-white/[0.05] hover:bg-white/[0.09] border border-white/10 rounded-xl text-xs font-semibold text-slate-200 transition-all cursor-pointer shadow-sm hover:border-indigo-500/50"
          >
            <Database className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            <span className="truncate max-w-[150px] sm:max-w-[200px]">
              {currentDataset?.name || 'Select Dataset'}
            </span>
            <span className="hidden sm:inline-block px-1.5 py-0.5 rounded text-[10px] font-mono bg-white/5 text-indigo-300 border border-white/10">
              {currentDataset?.rowCount || 0} rows
            </span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          </button>

          {showDatasetMenu && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowDatasetMenu(false)}
              />
              <div className="absolute left-0 mt-2 w-80 backdrop-blur-2xl bg-[#0e1017]/95 border border-white/10 rounded-2xl shadow-2xl z-50 py-2 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="px-3 py-2 border-b border-white/10 flex items-center justify-between">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Switch Active Dataset
                  </span>
                  <button
                    onClick={() => {
                      setShowDatasetMenu(false);
                      setCurrentRoute('/datasets/upload');
                    }}
                    className="text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 cursor-pointer"
                  >
                    <Plus className="w-3 h-3" /> Upload New
                  </button>
                </div>

                <div className="max-h-72 overflow-y-auto py-1">
                  {(!datasets || datasets.length === 0) ? (
                    <div className="p-4 text-center">
                      <p className="text-xs text-slate-400">No datasets uploaded yet</p>
                      <button
                        onClick={() => {
                          setShowDatasetMenu(false);
                          setCurrentRoute('/datasets/upload');
                        }}
                        className="mt-2.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors cursor-pointer"
                      >
                        Upload First Dataset
                      </button>
                    </div>
                  ) : (
                    datasets.map((ds) => {
                      const isSelected = ds.id === currentDataset?.id;
                      return (
                        <button
                          key={ds.id}
                          onClick={() => {
                            setCurrentDatasetById(ds.id);
                            setShowDatasetMenu(false);
                            showToast('success', 'Active Dataset Switched', ds.name);
                          }}
                          className={`w-full text-left px-3 py-2.5 flex items-start gap-2.5 hover:bg-white/5 transition-colors cursor-pointer ${
                            isSelected ? 'bg-indigo-950/40 border-l-2 border-indigo-500' : ''
                          }`}
                        >
                          <Database
                            className={`w-4 h-4 mt-0.5 shrink-0 ${
                              isSelected ? 'text-indigo-400' : 'text-slate-500'
                            }`}
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <p
                                className={`text-xs font-semibold truncate ${
                                  isSelected ? 'text-indigo-200' : 'text-slate-200'
                                }`}
                              >
                                {ds.name}
                              </p>
                              {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400 shrink-0" />}
                            </div>
                            <p className="text-[11px] text-slate-400 truncate mt-0.5">
                              {ds.domain || `${ds.columnCount} columns`} • {ds.rowCount} observations
                            </p>
                          </div>
                        </button>
                      );
                    })
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Middle section: Global Contextual Search */}
      <div className="hidden lg:flex items-center flex-1 max-w-md mx-6">
        <form onSubmit={handleSearchSubmit} className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={`Search across ${currentDataset?.columnCount || 0} dimensions, metrics, or anomalies...`}
            className="w-full pl-9 pr-4 py-1.5 backdrop-blur-md bg-white/[0.04] border border-white/10 rounded-xl text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:bg-white/[0.07] transition-all"
          />
        </form>
      </div>

      {/* Right section: AI Status, Action buttons, Notifications, Profile */}
      <div className="flex items-center gap-2.5">
        {/* AI Engine Status pill */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-400 font-medium backdrop-blur-md">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>AI Statistical Engine Ready</span>
        </div>

        {/* Upload Dataset Shortcut */}
        <button
          onClick={() => setCurrentRoute('/datasets/upload')}
          className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all cursor-pointer"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>Upload</span>
        </button>

        {/* AI Chat Shortcut */}
        <button
          onClick={() => setCurrentRoute('/chat', currentDataset?.id)}
          className={`p-2 rounded-xl border transition-all cursor-pointer backdrop-blur-md ${
            currentRoute === '/chat'
              ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/25'
              : 'bg-white/5 text-indigo-300 border-white/10 hover:bg-white/10'
          }`}
          title="Open AI Data Analyst Chat"
        >
          <Sparkles className="w-4 h-4" />
        </button>

        {/* Notifications */}
        <button
          onClick={() => showToast('info', 'System Notifications', '3 automated statistical correlations generated.')}
          className="p-2 rounded-xl backdrop-blur-md bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 transition-colors relative cursor-pointer"
          aria-label="Notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-indigo-500 ring-2 ring-[#0A0B10]" />
        </button>

        {/* User Profile Menu */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-1 rounded-xl hover:bg-white/5 transition-colors cursor-pointer"
          >
            <img
              src={user?.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80'}
              alt={user?.name || 'User'}
              className="w-8 h-8 rounded-xl object-cover border border-indigo-500/40"
              referrerPolicy="no-referrer"
            />
          </button>

          {showUserMenu && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowUserMenu(false)}
              />
              <div className="absolute right-0 mt-2 w-56 backdrop-blur-2xl bg-[#0e1017]/95 border border-white/10 rounded-2xl shadow-2xl z-50 py-1 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="px-3.5 py-2.5 border-b border-white/10">
                  <p className="text-xs font-semibold text-slate-200 truncate">{user?.name || 'Analyst'}</p>
                  <p className="text-[11px] text-slate-400 truncate">{user?.email || 'user@domain.com'}</p>
                  <span className="mt-1.5 inline-block px-1.5 py-0.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 rounded text-[10px] font-semibold">
                    {user?.plan || 'Enterprise'} Plan
                  </span>
                </div>

                <button
                  onClick={() => {
                    setShowUserMenu(false);
                    setCurrentRoute('/profile');
                  }}
                  className="w-full text-left px-3.5 py-2 text-xs text-slate-300 hover:bg-white/5 flex items-center gap-2 cursor-pointer"
                >
                  <User className="w-3.5 h-3.5 text-slate-400" /> My Profile
                </button>

                <button
                  onClick={() => {
                    setShowUserMenu(false);
                    setCurrentRoute('/settings');
                  }}
                  className="w-full text-left px-3.5 py-2 text-xs text-slate-300 hover:bg-white/5 flex items-center gap-2 cursor-pointer"
                >
                  <Settings className="w-3.5 h-3.5 text-slate-400" /> Platform Settings
                </button>

                <div className="border-t border-white/10 my-1" />

                <button
                  onClick={() => {
                    setShowUserMenu(false);
                    logout();
                  }}
                  className="w-full text-left px-3.5 py-2 text-xs text-rose-400 hover:bg-rose-950/30 flex items-center gap-2 cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" /> Log Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
