from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

CleaningIssueType = Literal[
    'missing_values',
    'duplicate_rows',
    'incorrect_types',
    'inconsistent_categories',
    'suspicious_values',
    'possible_outliers'
]

CleaningActionType = Literal[
    'impute_mean',
    'impute_median',
    'impute_mode',
    'impute_constant',
    'impute_ffill',
    'drop_missing_rows',
    'drop_column',
    'drop_duplicates',
    'standardize_casing',
    'strip_whitespace',
    'cast_to_numeric',
    'cast_to_datetime',
    'cap_outliers_iqr',
    'remove_outliers',
    'replace_suspicious_values'
]

RecommendationStatus = Literal['pending', 'approved', 'rejected']

class CleaningRecommendation(BaseModel):
    id: str
    issue: CleaningIssueType
    column: Optional[str] = None
    affected_rows: int = Field(ge=0, description="Count of rows affected by this issue")
    affected_percentage: float = Field(ge=0.0, le=100.0, description="Percentage of rows affected")
    suggested_action: str = Field(description="Clear human-readable description of suggested fix")
    action_type: CleaningActionType = Field(description="Machine-executable action type")
    reason: str = Field(description="Statistical and analytical justification for this recommendation")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters required for deterministic Python execution")
    status: RecommendationStatus = "pending"

class CleaningAuditReport(BaseModel):
    dataset_id: str
    total_issues_found: int
    health_score_before: float
    recommendations: List[CleaningRecommendation] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ApplyTransformationsRequest(BaseModel):
    approved_recommendation_ids: List[str] = Field(..., description="List of recommendation IDs approved by the user")
    save_as_new_dataset: bool = Field(default=False, description="If True, saves as new dataset instead of in-place transformation")
    new_dataset_name: Optional[str] = Field(default=None, description="Name for newly cloned dataset if save_as_new_dataset is True")

class AppliedActionDetail(BaseModel):
    recommendation_id: str
    action_type: CleaningActionType
    column: Optional[str] = None
    description: str
    rows_modified: int

class TransformationResult(BaseModel):
    dataset_id: str
    actions_applied_count: int
    rows_before: int
    rows_after: int
    columns_before: int
    columns_after: int
    health_score_before: float
    health_score_after: float
    applied_actions: List[AppliedActionDetail] = Field(default_factory=list)
    preview_rows: List[Dict[str, Any]] = Field(default_factory=list)
    executed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
