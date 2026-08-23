from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

VisualChartType = Literal[
    'line',
    'bar',
    'scatter',
    'histogram',
    'box_plot',
    'heatmap',
    'kpi_card',
    'donut',
    'area'
]

ColorTheme = Literal[
    'indigo_modern',
    'emerald_growth',
    'sunset_amber',
    'cyber_neon',
    'slate_executive'
]

AggregationFunction = Literal['sum', 'mean', 'median', 'count', 'min', 'max']

class VisualKPI(BaseModel):
    id: str
    title: str
    key: str
    value: float
    formatted_value: str
    aggregation: AggregationFunction
    trend_indicator: Optional[str] = None
    subtext: str

class ChartSeriesConfig(BaseModel):
    name: str
    data_key: str
    color: Optional[str] = None
    series_type: Optional[str] = None

class BoxPlotStats(BaseModel):
    column: str
    min: float
    q1: float
    median: float
    q3: float
    max: float
    iqr: float
    outliers: List[float] = Field(default_factory=list)

class HeatmapCell(BaseModel):
    x: str
    y: str
    value: float

class VisualChartConfig(BaseModel):
    chart_type: VisualChartType
    title: str
    subtitle: Optional[str] = None
    x_axis_key: str
    x_axis_label: Optional[str] = None
    y_axis_key: str
    y_axis_label: Optional[str] = None
    group_by: Optional[str] = None
    series: List[ChartSeriesConfig] = Field(default_factory=list)
    color_palette: List[str] = Field(default_factory=list)
    show_legend: bool = True
    show_grid: bool = True
    is_stacked: bool = False
    card_width: Literal['full', 'half', 'third'] = 'half'

class VisualChart(BaseModel):
    id: str
    config: VisualChartConfig
    data: List[Dict[str, Any]] = Field(default_factory=list)
    storytelling_caption: str = Field(description="Auto-generated analytical caption explaining key takeaway")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def chart_type(self) -> VisualChartType:
        return self.config.chart_type

class DashboardLayout(BaseModel):
    theme: ColorTheme = 'indigo_modern'
    kpi_cards: List[VisualKPI] = Field(default_factory=list)
    charts: List[VisualChart] = Field(default_factory=list)

class VisualizationDashboardResponse(BaseModel):
    dataset_id: str
    dataset_name: str
    total_charts: int
    theme: ColorTheme
    kpi_cards: List[VisualKPI] = Field(default_factory=list)
    charts: List[VisualChart] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CustomChartRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="Natural language prompt, e.g., 'Show latency by sensor zone'")
    preferred_chart_type: Optional[VisualChartType] = None
    dimension_column: Optional[str] = None
    metric_column: Optional[str] = None
    aggregation: AggregationFunction = 'sum'
    secondary_metric_column: Optional[str] = None

class CustomChartResponse(BaseModel):
    dataset_id: str
    query: Optional[str] = None
    chart: VisualChart
    explanation: str
