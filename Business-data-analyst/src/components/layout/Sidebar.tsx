import React from 'react';
import { useApp } from '../../context/AppContext';
import {
  LayoutDashboard,
  FolderKanban,
  UploadCloud,
  TableProperties,
  BarChart3,
  Lightbulb,
  CheckSquare,
  TrendingUp,
  MessageSquareCode,
  FileText,
  Settings,
  Sparkles,
  Layers,
  ChevronRight
} from 'lucide-react';

interface SidebarProps {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ mobileOpen, onMobileClose }) => {
  const { currentRoute, currentDataset, setCurrentRoute } = useApp();

  const navItems = [
    {
      label: 'Core Analytics',
      items: [
        {
          name: 'Executive Dashboard',
          route: '/dashboard',
          icon: LayoutDashboard,
          badge: null
        },
        {
          name: 'Workspace Projects',
          route: '/projects',
          icon: FolderKanban,
          badge: null
        },
        {
          name: 'Upload Dataset',
          route: '/datasets/upload',
          icon: UploadCloud,
          badge: null
        }
      ]
    },
    {
      label: 'Deep Intelligence',
      items: [
        {
          name: 'Dataset Explorer',
          route: '/datasets',
          param: currentDataset?.id,
          icon: TableProperties,
          badge: currentDataset ? `${currentDataset.columnCount} cols` : null
        },
        {
          name: 'Dynamic Analytics',
          route: '/analytics',
          param: currentDataset?.id,
          icon: BarChart3,
          badge: null
        },
        {
          name: 'AI Insights',
          route: '/insights',
          param: currentDataset?.id,
          icon: Lightbulb,
          badge: 'AI'
        },
        {
          name: 'Action Recommendations',
          route: '/recommendations',
          param: currentDataset?.id,
          icon: CheckSquare,
          badge: null
        },
        {
          name: 'Predictive Forecast',
          route: '/forecast',
          param: currentDataset?.id,
          icon: TrendingUp,
          badge: '95% CI'
        },
        {
          name: 'AI Analyst Chat',
          route: '/chat',
          param: currentDataset?.id,
          icon: MessageSquareCode,
          badge: 'Live'
        }
      ]
    },
    {
      label: 'Governance & Output',
      items: [
        {
          name: 'Executive Reports',
          route: '/reports',
          icon: FileText,
          badge: null
        },
        {
          name: 'Platform Settings',
          route: '/settings',
          icon: Settings,
          badge: null
        }
      ]
    }
  ];

  const handleNavClick = (route: string, param?: string) => {
    setCurrentRoute(route, param);
    if (onMobileClose) onMobileClose();
  };

  return (
    <aside
      className={`fixed lg:sticky top-0 left-0 z-40 h-screen w-64 backdrop-blur-2xl bg-[#0A0B10]/85 border-r border-white/10 flex flex-col transition-transform duration-200 ${
        mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 px-5 flex items-center gap-3 border-b border-white/10">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-sky-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-display font-bold text-white text-base tracking-tight">
              InsightFlow
            </span>
            <span className="text-[10px] font-bold px-1.5 py-0.2 bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded">
              AI
            </span>
          </div>
          <p className="text-[10px] text-slate-400 font-medium">Business Data Analyst</p>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navItems.map((section) => (
          <div key={section.label}>
            <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500 font-mono">
              {section.label}
            </div>
            <div className="space-y-1">
              {section.items.map((item) => {
                const isActive =
                  currentRoute === item.route ||
                  (item.route !== '/dashboard' && currentRoute.startsWith(item.route));

                const Icon = item.icon;

                return (
                  <button
                    key={item.name}
                    onClick={() => handleNavClick(item.route, item.param)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer group ${
                      isActive
                        ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-bold'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Icon
                        className={`w-4 h-4 shrink-0 transition-colors ${
                          isActive ? 'text-white' : 'text-slate-400 group-hover:text-indigo-400'
                        }`}
                      />
                      <span className="truncate">{item.name}</span>
                    </div>

                    {item.badge && (
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          isActive
                            ? 'bg-white/20 text-white'
                            : 'bg-white/5 text-slate-400 border border-white/10 group-hover:bg-indigo-950 group-hover:text-indigo-300'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Dynamic Schema Active Card */}
      {currentDataset && (
        <div className="p-3.5 backdrop-blur-xl bg-white/[0.04] border border-white/10 m-3 rounded-2xl">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-300">
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              <span className="truncate max-w-[130px]">{currentDataset.name}</span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-1.5 text-[10px] font-mono text-slate-400 mt-2">
            <div className="bg-white/5 px-2 py-1 rounded-lg border border-white/5">
              <span className="text-slate-400 block text-[9px]">ROWS</span>
              <span className="text-indigo-300 font-bold">{currentDataset.rowCount}</span>
            </div>
            <div className="bg-white/5 px-2 py-1 rounded-lg border border-white/5">
              <span className="text-slate-400 block text-[9px]">COLUMNS</span>
              <span className="text-emerald-300 font-bold">{currentDataset.columnCount}</span>
            </div>
          </div>
          <button
            onClick={() => setCurrentRoute('/analytics', currentDataset.id)}
            className="w-full mt-2.5 py-1.5 text-[11px] font-medium text-indigo-300 hover:text-indigo-200 flex items-center justify-center gap-1 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 rounded-xl transition-colors cursor-pointer"
          >
            <span>Inspect Neural Profile</span>
            <ChevronRight className="w-3 h-3" />
          </button>
        </div>
      )}
    </aside>
  );
};
