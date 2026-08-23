from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

RecommendationType = Literal[
    'growth',
    'operational',
    'cost_reduction',
    'risk_mitigation',
    'data_governance'
]

PriorityTier = Literal['P0_critical', 'P1_high', 'P2_medium', 'P3_low']
MatrixQuadrant = Literal['quick_win', 'strategic_bet', 'tactical_fix', 'long_term']
RecommendationStatus = Literal['pending', 'accepted', 'rejected', 'in_progress', 'completed']

class ExecutionStep(BaseModel):
    step_number: int
    title: str
    action_item: str
    target_timeframe_days: int
    deliverable: str

class BusinessRecommendation(BaseModel):
    """
    Actionable business recommendation strictly following the 6-pillar framework:
    1. Problem
    2. Evidence (Empirical Python stats)
    3. Action (Clear operational directive)
    4. Priority (P0, P1, P2, P3)
    5. Reasoning (Analytical rationale)
    6. Limitations (Risk boundaries and non-guaranteed assumptions)
    """
    id: str
    type: RecommendationType
    title: str
    subtitle: str
    
    # 6 Core Required Pillars
    problem: str = Field(description="Identified business bottleneck, data hygiene defect, or untapped area")
    evidence: str = Field(description="Empirical statistical evidence derived strictly from verified calculations")
    action: str = Field(description="Concrete operational action to execute")
    priority: PriorityTier = Field(description="Priority ranking: P0_critical, P1_high, P2_medium, P3_low")
    reasoning: str = Field(description="Analytical business logic explaining why this action addresses the problem")
    limitations: str = Field(description="Operational assumptions, data constraints, and external risk factors (No guaranteed outcomes)")

    # Metadata & Prioritization
    matrix_quadrant: MatrixQuadrant
    impact_score: float = Field(ge=1.0, le=10.0)
    effort_score: float = Field(ge=1.0, le=10.0)
    priority_score: float = Field(ge=0.0, le=100.0)
    target_metric_or_dimension: str
    baseline_value: float
    projected_uplift_pct: float
    projected_impact_value: float
    formatted_impact: str
    action_steps: List[ExecutionStep] = Field(default_factory=list)
    suggested_owner: str
    confidence_score: float = Field(default=0.95, ge=0.0, le=1.0)
    status: RecommendationStatus = 'pending'
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Helper property for backwards compatibility with earlier tests
    @property
    def rationale_summary(self) -> str:
        return self.reasoning

class RecommendationReport(BaseModel):
    dataset_id: str
    dataset_name: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    executive_rationale: str
    total_recommendations: int
    quick_wins_count: int
    strategic_bets_count: int
    estimated_total_upside: str
    recommendations: List[BusinessRecommendation] = Field(default_factory=list)
    roadmap_summary: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = Field(
        default="All projected outcomes are modeled estimates based on historical statistical evidence and do not represent guaranteed business results."
    )

class RecommendationActionRequest(BaseModel):
    recommendation_id: str
    action: Literal['accept', 'reject', 'in_progress', 'completed']
    notes: Optional[str] = None

class CustomRecommendationQueryRequest(BaseModel):
    domain_focus: Optional[str] = None
    target_goal: Optional[str] = None
    query: Optional[str] = None

class CustomRecommendationQueryResponse(BaseModel):
    dataset_id: str
    query: Optional[str] = None
    recommendations: List[BusinessRecommendation]
    strategic_synthesis: str
