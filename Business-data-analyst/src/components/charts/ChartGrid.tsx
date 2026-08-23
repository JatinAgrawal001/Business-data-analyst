import React from 'react';
import { Chart } from '../../types';
import { DynamicChart } from './DynamicChart';

interface ChartGridProps {
  charts: Chart[];
}

export const ChartGrid: React.FC<ChartGridProps> = ({ charts }) => {
  if (!charts || charts.length === 0) return null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      {charts.map((chart) => (
        <DynamicChart key={chart.id} chart={chart} />
      ))}
    </div>
  );
};
