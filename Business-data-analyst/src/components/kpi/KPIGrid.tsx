import React from 'react';
import { KPI } from '../../types';
import { KPICard } from './KPICard';

interface KPIGridProps {
  kpis: KPI[];
  onKPIClick?: (kpi: KPI) => void;
}

export const KPIGrid: React.FC<KPIGridProps> = ({ kpis, onKPIClick }) => {
  if (!kpis || kpis.length === 0) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((kpi) => (
        <KPICard key={kpi.id} kpi={kpi} onClick={() => onKPIClick?.(kpi)} />
      ))}
    </div>
  );
};
