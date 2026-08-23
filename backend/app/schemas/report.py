from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

ReportSectionType = Literal[
    'executive_summary',
    'dataset_overview',
    'data_quality',
    'kpi_grid',
    'chart_view',
    'key_insights',
    'risks_list',
    'recommendations_table',
    'forecast_view',
    'limitations_view',
    'markdown_text'
]

ReportCadence = Literal['on_demand', 'daily', 'weekly', 'monthly', 'quarterly']
ReportStatus = Literal['draft', 'published', 'archived']

class ReportSection(BaseModel):
    id: str
    title: str
    type: ReportSectionType
    content: Any = Field(description="Dynamic section payload (KPIs, Charts, Insights, Recommendations, Forecast, Quality, Overview, or Limitations)")

class GenerateReportRequest(BaseModel):
    dataset_id: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    include_kpis: bool = True
    include_charts: bool = True
    include_insights: bool = True
    include_recommendations: bool = True
    include_forecast: bool = True
    cadence: ReportCadence = 'on_demand'

class ExecutiveReport(BaseModel):
    id: str
    project_id: str
    dataset_id: str
    dataset_name: str = Field(default="Dataset")
    title: str
    subtitle: str
    executive_summary: str
    key_takeaways: List[str] = Field(default_factory=list)
    sections: List[ReportSection] = Field(default_factory=list)
    author: str = Field(default="Lead Data Intelligence Analyst")
    status: ReportStatus = 'published'
    format: str = 'pdf'
    cadence: ReportCadence = 'on_demand'
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    disclaimer: str = Field(
        default="All statistical figures, insights, and predictive trajectories are computed deterministically via Python analytics and explained via NVIDIA NIM AI. Forward projections represent mathematical models and do not guarantee business results."
    )

class ReportExportResponse(BaseModel):
    report_id: str
    title: str
    format: Literal['html', 'markdown', 'json']
    exported_content: str
    file_name: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
