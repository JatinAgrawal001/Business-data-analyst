from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

ColumnDataType = Literal['numeric', 'categorical', 'datetime', 'boolean', 'text', 'id']

class HistogramBucket(BaseModel):
    bucket: str
    count: int
    percentage: float

class CategoryFrequency(BaseModel):
    label: str
    count: int
    percentage: float
    cumulative_percentage: float

class QuantilesSummary(BaseModel):
    p5: float
    p25: float  # Q1
    p50: float  # Median
    p75: float  # Q3
    p95: float
    iqr: float

class OutlierSummary(BaseModel):
    iqr_lower_bound: float
    iqr_upper_bound: float
    outlier_count: int
    outlier_percentage: float
    outlier_samples: List[float] = Field(default_factory=list)

class NumericStats(BaseModel):
    min: float
    max: float
    mean: float
    median: float
    std_dev: float
    variance: float
    sum: float
    skewness: float
    kurtosis: float
    zeros_count: int
    zeros_percentage: float
    negatives_count: int
    quantiles: QuantilesSummary
    outliers: OutlierSummary
    distribution: List[HistogramBucket] = Field(default_factory=list)

class CategoricalStats(BaseModel):
    cardinality: int
    distinct_ratio: float
    mode: Optional[str] = None
    entropy: float
    top_categories: List[CategoryFrequency] = Field(default_factory=list)

class DatetimeStats(BaseModel):
    min_date: str
    max_date: str
    timespan_days: float
    detected_frequency: Optional[str] = None

class TextStats(BaseModel):
    min_length: int
    max_length: int
    avg_length: float
    is_unique_id: bool = False

class ColumnDetailedProfile(BaseModel):
    name: str
    key: str
    original_name: str
    data_type: ColumnDataType
    inferred_confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    null_count: int
    null_percentage: float
    unique_count: int
    total_count: int
    cardinality: int
    distinct_ratio: float
    is_identifier: bool = False
    is_potential_metric: bool = False
    numeric_stats: Optional[NumericStats] = None
    categorical_stats: Optional[CategoricalStats] = None
    datetime_stats: Optional[DatetimeStats] = None
    text_stats: Optional[TextStats] = None
    warnings: List[str] = Field(default_factory=list)

class PotentialMetric(BaseModel):
    name: str
    key: str
    data_type: str = "numeric"
    sum: float
    mean: float
    median: float
    min: float
    max: float
    std_dev: float
    reason: str

class MissingValuesSummary(BaseModel):
    total_cells: int
    missing_cells: int
    missing_percentage: float
    columns_with_missing: List[str] = Field(default_factory=list)

class DuplicateSummary(BaseModel):
    duplicate_rows: int
    duplicate_percentage: float

class QualityWarning(BaseModel):
    column: Optional[str] = None
    warning_type: Literal['high_missing', 'constant_value', 'high_cardinality', 'severe_outliers', 'duplicate_rows', 'skewed_distribution']
    message: str
    severity: Literal['critical', 'warning', 'info']

class DataQualityReport(BaseModel):
    health_score: float = Field(ge=0.0, le=100.0, description="Overall dataset health rating 0-100")
    total_cells: int
    missing_cells: int
    missing_percentage: float
    complete_rows_count: int
    complete_rows_percentage: float
    duplicate_rows_count: int
    duplicate_rows_percentage: float
    memory_usage_bytes: int
    warnings: List[QualityWarning] = Field(default_factory=list)

class CorrelationPair(BaseModel):
    column_x: str
    column_y: str
    pearson_r: float
    spearman_r: float
    strength: Literal['very_strong', 'strong', 'moderate', 'weak', 'none']
    direction: Literal['positive', 'negative', 'neutral']

class DatasetProfile(BaseModel):
    """
    Complete structured profile of an arbitrary business dataset computed deterministically with Pandas/NumPy.
    """
    dataset_id: str
    project_id: str
    name: str
    file_type: str
    row_count: int
    column_count: int
    numeric_columns: List[str] = Field(default_factory=list)
    categorical_columns: List[str] = Field(default_factory=list)
    datetime_columns: List[str] = Field(default_factory=list)
    identifier_columns: List[str] = Field(default_factory=list)
    potential_metrics: List[PotentialMetric] = Field(default_factory=list)
    missing_values_summary: MissingValuesSummary
    duplicate_summary: DuplicateSummary
    quality_report: DataQualityReport
    columns: List[ColumnDetailedProfile] = Field(default_factory=list)
    descriptive_stats: Dict[str, NumericStats] = Field(default_factory=dict)
    strong_correlations: List[CorrelationPair] = Field(default_factory=list)
    correlation_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    profiled_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    execution_time_ms: float

# Alias for backward compatibility
ComprehensiveDatasetProfile = DatasetProfile
