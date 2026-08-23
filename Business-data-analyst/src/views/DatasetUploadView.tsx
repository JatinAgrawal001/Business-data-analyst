import React from 'react';
import { useApp } from '../context/AppContext';
import { DatasetUploader } from '../components/datasets/DatasetUploader';
import { ArrowLeft, Database } from 'lucide-react';

export const DatasetUploadView: React.FC = () => {
  const { setCurrentRoute } = useApp();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={() => setCurrentRoute('/dashboard')}
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Dashboard</span>
        </button>
      </div>

      <DatasetUploader
        onSuccess={(id) => {
          setCurrentRoute('/analytics', id);
        }}
      />
    </div>
  );
};
