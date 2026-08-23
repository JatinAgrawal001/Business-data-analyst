from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

TrendDirection = Literal['bullish_expansion', 'moderate_growth', 'bearish_contraction', 'stable']
ForecastConfidenceLevel = Literal['high', 'moderate', 'low', 'unreliable']

class SuitabilityCheckDetail(BaseModel):
    check_name: str
    passed: bool
    details: str
    observed_value: Optional[Any] = None
    required_threshold: Optional[Any] = None

class ForecastingSuitabilityReport(BaseModel):
    is_suitable: bool
    summary: str
    datetime_column_found: bool
    datetime_column_name: Optional[str] = None
    numeric_metric_found: bool
    numeric_metric_name: Optional[str] = None
    historical_periods_count: int
    detected_frequency: Optional[str] = None
    has_regular_intervals: bool
    missing_periods_gap_ratio: float = Field(ge=0.0, le=1.0)
    train_test_split_viable: bool
    checks: List[SuitabilityCheckDetail] = Field(default_factory=list)
    unsuitability_reasons: List[str] = Field(default_factory=list)
    remediation_suggestions: List[str] = Field(default_factory=list)

    @property
    def train_test_viable(self) -> bool:
        return self.train_test_split_viable

class ForecastPoint(BaseModel):
    period_index: int
    period_label: str
    timestamp: str
    is_historical: bool
    is_test_split: bool = False
    actual_value: Optional[float] = None
    forecast_value: float
    lower_bound_95: float
    upper_bound_95: float

class ModelEvaluationMetrics(BaseModel):
    model_name: str
    train_rmse: float
    train_mae: float
    test_rmse: Optional[float] = None
    test_mae: Optional[float] = None
    test_mape: Optional[float] = None
    r_squared: float
    is_champion: bool = False

class BaselineComparisonSummary(BaseModel):
    baseline_model_name: str = "Naive Last-Observed Baseline"
    baseline_test_rmse: float
    champion_model_name: str
    champion_test_rmse: float
    rmse_improvement_pct: float
    comparison_summary: str
    candidate_models_evaluated: List[ModelEvaluationMetrics] = Field(default_factory=list)

class DriverImportance(BaseModel):
    feature_name: str
    importance_score: float = Field(ge=0.0, le=1.0)
    direction: Literal['positive', 'negative']
    standardized_beta: float
    business_takeaway: str

class ValidatedTimeSeriesForecast(BaseModel):
    """
    Complete forecast output strictly returned only when dataset passes all suitability checks.
    """
    is_suitable: bool = True
    suitability_report: ForecastingSuitabilityReport
    target_metric: str
    time_dimension: str
    detected_frequency: str
    historical_points_count: int
    train_points_count: int
    test_points_count: int
    forecast_horizon_periods: int
    trend_direction: TrendDirection
    annualized_growth_rate_pct: float
    baseline_recent_value: float
    terminal_forecast_value: float
    projected_net_change_pct: float
    model_used: str
    evaluation_metrics: ModelEvaluationMetrics
    baseline_comparison: BaselineComparisonSummary
    predicted_values: List[ForecastPoint] = Field(default_factory=list)
    top_drivers: List[DriverImportance] = Field(default_factory=list)
    limitations: str
    natural_language_summary: str

    @property
    def model_metrics(self) -> ModelEvaluationMetrics:
        return self.evaluation_metrics

    @property
    def forecast_points(self) -> List[ForecastPoint]:
        return self.predicted_values

class InappropriateForecastResponse(BaseModel):
    is_suitable: bool = False
    suitability_report: ForecastingSuitabilityReport
    message: str = "Forecasting is mathematically inappropriate for this dataset."
    detailed_explanation: str
    remediation_steps: List[str]

class WhatIfScenarioRequest(BaseModel):
    target_metric: Optional[str] = None
    feature_adjustments: Dict[str, float] = Field(
        description="Dictionary mapping feature names to percentage shifts, e.g. {'marketing_spend': 1.15, 'pricing': 0.95}"
    )

class WhatIfScenarioResponse(BaseModel):
    target_metric: str
    baseline_predicted_value: float
    simulated_predicted_value: float
    absolute_delta: float
    percentage_change: float
    simulated_adjustments: Dict[str, float]
    strategic_interpretation: str

class CustomForecastRequest(BaseModel):
    target_metric: Optional[str] = None
    time_dimension: Optional[str] = None
    forecast_periods: int = Field(default=6, ge=1, le=36)

class PredictionReport(BaseModel):
    dataset_id: str
    dataset_name: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_suitable: bool
    suitability_report: ForecastingSuitabilityReport
    executive_summary: str
    primary_forecast: Optional[ValidatedTimeSeriesForecast] = None
    secondary_forecasts: List[ValidatedTimeSeriesForecast] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    scenario_planning_guidance: str
    disclaimer: str = Field(
        default="All statistical forecasts and confidence intervals are probabilistic projections computed via mathematical regression models and do not guarantee future performance."
    )

TimeSeriesForecast = ValidatedTimeSeriesForecast
ModelMetrics = ModelEvaluationMetrics
