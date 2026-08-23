from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.schemas.profiler import NumericStats, HistogramBucket, CategoryFrequency, OutlierSummary

ChartType = Literal['bar', 'line', 'area', 'scatter', 'donut', 'pie', 'radar', 'heatmap']

class KPIEntry(BaseModel):
    title: str
    key: str
    value: float
    formatted_value: str
    aggregation_type: Literal['sum', 'mean', 'median', 'count']
    metric_type: Literal['volume', 'average', 'ratio', 'count']
    description: str

class SegmentBreakdownEntry(BaseModel):
    category: str
    metric_sum: float
    metric_mean: float
    record_count: int
    percentage: float

class SegmentAnalysis(BaseModel):
    dimension_column: str
    metric_column: str
    top_segments: List[SegmentBreakdownEntry] = Field(default_factory=list)
    insight: str

class CategoryAnalysisEntry(BaseModel):
    column: str
    cardinality: int
    distinct_ratio: float
    mode: Optional[str] = None
    entropy: float
    top_categories: List[CategoryFrequency] = Field(default_factory=list)

class ColumnOutlierReport(BaseModel):
    column: str
    outlier_count: int
    outlier_percentage: float
    iqr_lower_bound: float
    iqr_upper_bound: float
    sample_outliers: List[float] = Field(default_factory=list)
    severity: Literal['severe', 'moderate', 'none']

class TimeSeriesPoint(BaseModel):
    period: str
    value: float
    record_count: int

class TimeSeriesTrend(BaseModel):
    time_column: str
    metric_column: str
    granularity: str = "daily"
    trend_direction: Literal['upward', 'downward', 'stable', 'volatile']
    growth_rate: float
    data_points: List[TimeSeriesPoint] = Field(default_factory=list)
    insight: str

class CorrelationInsight(BaseModel):
    feature_x: str
    feature_y: str
    pearson_r: float
    spearman_r: float
    strength: Literal['very_strong', 'strong', 'moderate', 'weak', 'none']
    direction: Literal['positive', 'negative', 'neutral']
    interpretation: str

class CorrelationSummary(BaseModel):
    matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    ranked_pairs: List[CorrelationInsight] = Field(default_factory=list)

class ChartRecommendation(BaseModel):
    id: str
    title: str
    chart_type: ChartType
    x_axis: str
    y_axis: str
    group_by: Optional[str] = None
    description: str
    data: List[Dict[str, Any]] = Field(default_factory=list)

class EDAInsight(BaseModel):
    id: str
    title: str
    category: Literal['trend', 'correlation', 'segment', 'anomaly', 'performance']
    priority: Literal['high', 'medium', 'low']
    description: str
    action_suggested: Optional[str] = None

class EDASummary(BaseModel):
    overview: str
    total_rows: int
    total_columns: int
    numeric_columns_count: int
    categorical_columns_count: int
    datetime_columns_count: int
    primary_metric: Optional[str] = None
    primary_dimension: Optional[str] = None
    key_takeaways: List[str] = Field(default_factory=list)

class EDAReport(BaseModel):
    """
    Complete dynamic Exploratory Data Analysis report calculated deterministically via Python/Pandas.
    Works for any arbitrary business dataset without fixed column naming assumptions.
    """
    dataset_id: str
    dataset_name: str
    summary: EDASummary
    kpis: List[KPIEntry] = Field(default_factory=list)
    descriptive_statistics: Dict[str, NumericStats] = Field(default_factory=dict)
    distributions: Dict[str, List[HistogramBucket]] = Field(default_factory=dict)
    category_analysis: List[CategoryAnalysisEntry] = Field(default_factory=list)
    time_trends: Optional[TimeSeriesTrend] = None
    group_by_analysis: List[SegmentAnalysis] = Field(default_factory=list)
    outlier_analysis: List[ColumnOutlierReport] = Field(default_factory=list)
    correlations: CorrelationSummary = Field(default_factory=CorrelationSummary)
    chart_recommendations: List[ChartRecommendation] = Field(default_factory=list)
    insights: List[EDAInsight] = Field(default_factory=list)
    execution_time_ms: float
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def segments(self) -> List[SegmentAnalysis]:
        return self.group_by_analysis

    @property
    def time_series(self) -> Optional[TimeSeriesTrend]:
        return self.time_trends

# Backwards compatibility alias
DynamicEDAResult = EDAReport
