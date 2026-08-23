export type ColumnDataType = 'numeric' | 'categorical' | 'datetime' | 'boolean' | 'text' | 'id';

export interface DatasetColumnSummary {
  min?: number;
  max?: number;
  mean?: number;
  median?: number;
  stdDev?: number;
  uniqueCount: number;
  nullCount: number;
  totalCount: number;
  topCategories?: { label: string; count: number; percentage: number }[];
  distribution?: { bucket: string; count: number }[];
}

export interface DatasetColumn {
  name: string;
  key: string;
  originalName: string;
  dataType: ColumnDataType;
  summary?: DatasetColumnSummary;
  description?: string;
  isTarget?: boolean;
}

export interface Dataset {
  id: string;
  projectId: string;
  name: string;
  description: string;
  rowCount: number;
  columnCount: number;
  columns: DatasetColumn[];
  sampleRows: Record<string, any>[];
  allRows?: Record<string, any>[];
  sizeBytes: number;
  uploadedAt: string;
  fileType: 'csv' | 'json' | 'xlsx' | 'sql' | 'api';
  fileName?: string;
  storageBucket?: string;
  storagePath?: string;
  status: 'uploaded' | 'profiling' | 'ready' | 'error';
  domain?: string;
  tags?: string[];
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar: string;
  role: string;
  company: string;
  plan: 'Starter' | 'Professional' | 'Enterprise';
  createdAt: string;
  preferences: {
    theme: 'dark' | 'light' | 'system';
    emailAlerts: boolean;
    autoInsightDetection: boolean;
    defaultConfidenceInterval: number;
  };
}

export interface Project {
  id: string;
  name: string;
  description: string;
  datasetIds: string[];
  defaultDatasetId?: string;
  status: 'active' | 'archived' | 'analyzing';
  tags: string[];
  createdAt: string;
  updatedAt: string;
  memberCount: number;
}

export interface KPI {
  id: string;
  label: string;
  value: string | number;
  rawValue: number;
  changePercentage: number;
  trend: 'up' | 'down' | 'neutral';
  isPositive: boolean;
  description: string;
  category: string;
  primaryColumn?: string;
  iconType?: string;
  sparklineData?: number[];
  unit?: string;
}

export type ChartType = 'line' | 'bar' | 'area' | 'donut' | 'scatter' | 'heatmap' | 'composed' | 'radar';

export interface Chart {
  id: string;
  title: string;
  subtitle?: string;
  chartType: ChartType;
  xAxisKey: string;
  xAxisLabel?: string;
  yAxisKeys: string[];
  yAxisLabels?: string[];
  data: any[];
  description: string;
  aggregationType?: 'sum' | 'avg' | 'count' | 'distribution' | 'trend';
  columnReferences: string[];
  category?: string;
  colors?: string[];
}

export interface Insight {
  id: string;
  title: string;
  description: string;
  category: 'trend' | 'anomaly' | 'correlation' | 'distribution' | 'performance' | 'segment';
  priority: 'critical' | 'high' | 'medium' | 'low';
  score: number; // 0 - 100
  keyMetrics?: { label: string; value: string; change?: string }[];
  impact: string;
  actionRequired: boolean;
  relevantColumns: string[];
  createdAt: string;
  suggestedAction?: string;
}

export interface Recommendation {
  id: string;
  title: string;
  executiveSummary: string;
  detailedSteps: string[];
  expectedImpact: string;
  impactScore: number; // 0 - 100
  confidence: number; // 0 - 100
  difficulty: 'easy' | 'moderate' | 'hard';
  timeframe: string;
  category: string;
  status: 'new' | 'in_review' | 'implemented' | 'dismissed';
  metricsInfluenced: string[];
}

export interface ForecastDriver {
  factor: string;
  weight: number;
  direction: 'positive' | 'negative';
}

export interface ForecastDataPoint {
  timestamp: string;
  actual?: number;
  predicted?: number;
  lowerBound?: number;
  upperBound?: number;
  anomaly?: boolean;
}

export interface Forecast {
  id: string;
  targetMetricKey: string;
  targetMetricLabel: string;
  timeColumnKey: string;
  historicalData: { timestamp: string; actual: number }[];
  forecastData: { timestamp: string; predicted: number; lowerBound: number; upperBound: number }[];
  allPoints?: ForecastDataPoint[];
  confidenceInterval: number; // e.g. 95
  growthRate: number; // percentage
  modelUsed: string;
  horizonPeriods: number;
  scenarioMultipliers?: { optimistic: number; baseline: number; pessimistic: number };
  keyDrivers: ForecastDriver[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  suggestedQuestions?: string[];
  generatedChart?: Chart;
  sqlQuery?: string;
  dataFilter?: Record<string, any>;
  referenceColumns?: string[];
  isStreaming?: boolean;
}

export interface ReportSection {
  id: string;
  title: string;
  type: 'kpi_grid' | 'chart_view' | 'insights_list' | 'recommendations_table' | 'forecast_view' | 'narrative';
  content: any;
  config?: Record<string, any>;
}

export interface Report {
  id: string;
  projectId: string;
  datasetId: string;
  title: string;
  subtitle?: string;
  executiveSummary: string;
  generatedAt: string;
  author: string;
  sections: ReportSection[];
  status: 'published' | 'draft' | 'scheduled';
  format: 'pdf' | 'html' | 'presentation';
  cadence?: 'daily' | 'weekly' | 'monthly' | 'on_demand';
}

export interface CorrelationPair {
  colA: string;
  colB: string;
  coefficient: number;
  relationship: 'strong_positive' | 'moderate_positive' | 'neutral' | 'moderate_negative' | 'strong_negative';
  description: string;
}

export interface AnomalyItem {
  column: string;
  value: number | string;
  expectedValue: number | string;
  deviation: number;
  severity: 'critical' | 'high' | 'medium' | 'low';
}

export interface Analysis {
  id: string;
  datasetId: string;
  projectId: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progressPercentage: number;
  currentStep: string;
  kpis: KPI[];
  charts: Chart[];
  insights: Insight[];
  recommendations: Recommendation[];
  forecast: Forecast;
  forecasts?: Forecast[];
  statisticalSummary: {
    totalRecords: number;
    numericalColumnCount: number;
    categoricalColumnCount: number;
    dateColumnCount: number;
    dataQualityScore: number;
    completenessRate: number;
  };
  anomaliesDetectedCount: number;
  anomalies?: AnomalyItem[];
  correlationMatrix: CorrelationPair[];
  createdAt: string;
  completedAt?: string;
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  title: string;
  message?: string;
  duration?: number;
}
