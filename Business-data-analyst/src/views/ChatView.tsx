import React from 'react';
import { useApp } from '../context/AppContext';
import { AIChat } from '../components/chat/AIChat';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';
import { MessageSquareCode, Sparkles, Database } from 'lucide-react';

export const ChatView: React.FC = () => {
  const { currentDataset, datasets, setCurrentDatasetById, setCurrentRoute, isLoading } = useApp();

  if (isLoading && !currentDataset) {
    return <LoadingState message="Connecting to AI Data Analyst engine..." />;
  }

  if (!currentDataset) {
    return (
      <EmptyState
        title="No Dataset Selected for Chat"
        description="Select an active dataset or upload custom data to converse with the AI Data Analyst."
        actionText="Upload Dataset"
        onAction={() => setCurrentRoute('/datasets/upload')}
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Header Bar */}
      <div className="p-4 sm:p-5 rounded-2xl backdrop-blur-xl bg-white/[0.04] border border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 flex items-center justify-center">
            <MessageSquareCode className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold font-display text-white">
              AI Business Data Analyst Chat
            </h2>
            <p className="text-xs text-slate-400">
              Query schema dimensions, ask for automated multi-variable charts, or request SQL expressions.
            </p>
          </div>
        </div>

        {/* Dataset Switcher in Chat Header */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Dataset:</span>
          <select
            value={currentDataset.id}
            onChange={(e) => setCurrentDatasetById(e.target.value)}
            className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            {datasets.map((ds) => (
              <option key={ds.id} value={ds.id}>
                {ds.name} ({ds.rowCount} rows)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* AIChat Component */}
      <AIChat dataset={currentDataset} />
    </div>
  );
};
