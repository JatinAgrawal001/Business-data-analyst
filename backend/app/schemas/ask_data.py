from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.schemas.visualization import VisualChart

class DataTableResult(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int

class AskDataQueryRequest(BaseModel):
    query: str = Field(description="Natural language question about the dataset")
    conversation_id: Optional[str] = None
    focus_columns: Optional[List[str]] = Field(default_factory=list)

class AskDataQueryResponse(BaseModel):
    dataset_id: str
    query: str
    answered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    answer: str = Field(description="Comprehensive natural business language explanation synthesized via NVIDIA NIM")
    answer_markdown: str = Field(description="Backwards-compatible alias for answer")
    supporting_metrics: Dict[str, Any] = Field(
        description="Exact deterministic Python-computed values and aggregations (Source of Truth)"
    )
    relevant_columns: List[str] = Field(
        description="List of dataset columns utilized in answering the question",
        default_factory=list
    )
    direct_kpi_value: Optional[float] = None
    direct_kpi_formatted: Optional[str] = None
    data_table: Optional[DataTableResult] = None
    chart: Optional[VisualChart] = None
    suggested_followups: List[str] = Field(default_factory=list)
    conversation_id: Optional[str] = None
    execution_time_ms: float

    @property
    def python_verified_facts(self) -> Dict[str, Any]:
        return self.supporting_metrics

class StarterQuestion(BaseModel):
    id: str
    category: Literal['metric_summary', 'breakdown', 'trend', 'outlier', 'correlation']
    question: str
    rationale: str

class SuggestedQuestionsResponse(BaseModel):
    dataset_id: str
    starter_questions: List[StarterQuestion] = Field(default_factory=list)

class ChatHistoryMessage(BaseModel):
    id: str
    user_id: Optional[str] = None
    dataset_id: str
    role: Literal['user', 'assistant', 'system']
    content: str
    supporting_metrics: Optional[Dict[str, Any]] = None
    relevant_columns: Optional[List[str]] = None
    chart: Optional[VisualChart] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ChatHistoryResponse(BaseModel):
    dataset_id: str
    messages: List[ChatHistoryMessage] = Field(default_factory=list)
    total_messages: int
