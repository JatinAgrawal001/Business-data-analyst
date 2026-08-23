from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

InsightCategory = Literal[
    'key_insight',
    'trend',
    'anomaly',
    'risk',
    'opportunity'
]

InsightSeverity = Literal['critical', 'high', 'medium', 'low', 'info']
ActionTimeframe = Literal['immediate', 'short_term', 'long_term']
ImpactLevel = Literal['high', 'medium', 'low']
EffortLevel = Literal['low', 'medium', 'high']

class StrategicAction(BaseModel):
    id: str
    title: str
    description: str
    impact: ImpactLevel = 'high'
    effort: EffortLevel = 'medium'
    timeframe: ActionTimeframe = 'short_term'
    target_metric_or_dimension: Optional[str] = None
    expected_outcome: str

class GroundedInsightItem(BaseModel):
    """
    Insight item with strictly separated Python-calculated facts and NVIDIA natural language explanation.
    """
    id: str
    category: InsightCategory
    title: str
    headline: str
    python_verified_facts: Dict[str, Any] = Field(
        description="Exact deterministic values computed via Python (Pandas/NumPy) - Zero Hallucinated Numbers"
    )
    natural_language_explanation: str = Field(
        description="NVIDIA/ADK natural business language synthesis explaining the verified factual findings"
    )
    business_impact: str
    recommended_action: Optional[str] = None
    severity: InsightSeverity = 'info'
    confidence_score: float = Field(default=0.98, ge=0.0, le=1.0)
    metrics_involved: List[str] = Field(default_factory=list)

class StructuredInsightReport(BaseModel):
    """
    Complete structured insight report organizing findings across all 5 core dimensions:
    - key_insights
    - trends
    - anomalies
    - risks
    - opportunities
    """
    dataset_id: str
    dataset_name: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    executive_summary: str
    health_score: float
    total_insights: int
    key_insights: List[GroundedInsightItem] = Field(default_factory=list)
    trends: List[GroundedInsightItem] = Field(default_factory=list)
    anomalies: List[GroundedInsightItem] = Field(default_factory=list)
    risks: List[GroundedInsightItem] = Field(default_factory=list)
    opportunities: List[GroundedInsightItem] = Field(default_factory=list)
    strategic_recommendations: List[StrategicAction] = Field(default_factory=list)
    macro_outlook: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Helper property for backwards compatibility
    @property
    def insights(self) -> List[GroundedInsightItem]:
        return self.key_insights + self.trends + self.anomalies + self.risks + self.opportunities

# Alias for backwards compatibility
InsightReport = StructuredInsightReport
ExecutiveInsight = GroundedInsightItem

class QueryInsightRequest(BaseModel):
    focus_metric: Optional[str] = None
    focus_dimension: Optional[str] = None
    category: Optional[InsightCategory] = None
    query: Optional[str] = None

class QueryInsightResponse(BaseModel):
    dataset_id: str
    query: Optional[str] = None
    category: Optional[InsightCategory] = None
    insights: List[GroundedInsightItem]
    synthesis: str
