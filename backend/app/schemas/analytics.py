from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class KPI(BaseModel):
    id: str
    label: str
    value: Any
    rawValue: float
    changePercentage: float = 0.0
    trend: Literal['up', 'down', 'neutral'] = 'neutral'
    isPositive: bool = True
    description: str
    category: str
    primaryColumn: Optional[str] = None
    sparklineData: Optional[List[float]] = None
    unit: Optional[str] = None

class Chart(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = None
    chartType: Literal['line', 'bar', 'area', 'donut', 'scatter', 'heatmap', 'composed', 'radar'] = 'bar'
    xAxisKey: str
    xAxisLabel: Optional[str] = None
    yAxisKeys: List[str]
    yAxisLabels: Optional[List[str]] = None
    data: List[Dict[str, Any]]
    description: str
    aggregationType: Optional[Literal['sum', 'avg', 'count', 'distribution', 'trend']] = 'sum'
    columnReferences: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    colors: Optional[List[str]] = None

class Insight(BaseModel):
    id: str
    projectId: Optional[str] = None
    datasetId: Optional[str] = None
    userId: Optional[str] = None
    title: str
    description: str
    category: Literal['trend', 'anomaly', 'correlation', 'distribution', 'performance', 'segment'] = 'trend'
    priority: Literal['critical', 'high', 'medium', 'low'] = 'medium'
    score: float = Field(ge=0, le=100, default=85.0)
    keyMetrics: Optional[List[Dict[str, Any]]] = None
    impact: str = ""
    actionRequired: bool = False
    relevantColumns: List[str] = Field(default_factory=list)
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    suggestedAction: Optional[str] = None

class Recommendation(BaseModel):
    id: str
    projectId: Optional[str] = None
    datasetId: Optional[str] = None
    userId: Optional[str] = None
    title: str
    executiveSummary: str
    detailedSteps: List[str] = Field(default_factory=list)
    expectedImpact: str
    impactScore: float = Field(ge=0, le=100, default=80.0)
    confidence: float = Field(ge=0, le=100, default=85.0)
    difficulty: Literal['easy', 'moderate', 'hard'] = 'moderate'
    timeframe: str = "30 Days"
    category: str = "Growth"
    status: Literal['new', 'in_review', 'implemented', 'dismissed'] = 'new'
    metricsInfluenced: List[str] = Field(default_factory=list)

class ForecastDriver(BaseModel):
    factor: str
    weight: float
    direction: Literal['positive', 'negative']

class ForecastPoint(BaseModel):
    timestamp: str
    predicted: float
    lowerBound: float
    upperBound: float

class Forecast(BaseModel):
    id: str
    projectId: Optional[str] = None
    datasetId: Optional[str] = None
    userId: Optional[str] = None
    targetMetricKey: str
    targetMetricLabel: str
    timeColumnKey: str = "period"
    historicalData: List[Dict[str, Any]] = Field(default_factory=list)
    forecastData: List[ForecastPoint] = Field(default_factory=list)
    confidenceInterval: float = 95.0
    growthRate: float = 0.0
    modelUsed: str = "Auto-Regressive Polynomial Trend"
    horizonPeriods: int = 6
    keyDrivers: List[ForecastDriver] = Field(default_factory=list)

class ChatMessage(BaseModel):
    id: str
    userId: Optional[str] = None
    datasetId: Optional[str] = None
    role: Literal['user', 'assistant', 'system']
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    suggestedQuestions: Optional[List[str]] = None
    generatedChart: Optional[Chart] = None

class ReportSection(BaseModel):
    id: str
    title: str
    type: Literal['kpi_grid', 'chart_view', 'insights_list', 'recommendations_table', 'forecast_view', 'narrative']
    content: Any = Field(default_factory=dict)

class Report(BaseModel):
    id: str
    projectId: str
    datasetId: str
    userId: Optional[str] = None
    title: str
    subtitle: Optional[str] = None
    executiveSummary: str
    sections: List[ReportSection] = Field(default_factory=list)
    keyTakeaways: List[str] = Field(default_factory=list)
    methodologies: List[str] = Field(default_factory=list)
    generatedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    author: str = "InsightFlow Analyst"
    status: Literal['draft', 'published', 'archived'] = 'published'

class Analysis(BaseModel):
    id: str
    projectId: str
    datasetId: str
    userId: Optional[str] = None
    status: Literal['queued', 'running', 'completed', 'failed'] = 'completed'
    progressPercentage: int = 100
    currentStep: str = "Completed"
    kpis: List[KPI] = Field(default_factory=list)
    charts: List[Chart] = Field(default_factory=list)
    insights: List[Insight] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    forecast: Optional[Forecast] = None
    completedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
