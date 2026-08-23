from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class UserPreferences(BaseModel):
    theme: Literal['dark', 'light', 'system'] = 'dark'
    emailAlerts: bool = True
    autoInsightDetection: bool = True
    defaultConfidenceInterval: int = 95

class User(BaseModel):
    id: str
    name: str
    email: str
    avatar: Optional[str] = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80"
    role: str = "Lead Business Data Analyst"
    company: str = "Enterprise Workspace"
    plan: Literal['Starter', 'Professional', 'Enterprise'] = 'Enterprise'
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    preferences: UserPreferences = Field(default_factory=UserPreferences)

class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    datasetIds: List[str] = Field(default_factory=list)
    defaultDatasetId: Optional[str] = None
    status: Literal['active', 'archived', 'analyzing'] = 'active'
    tags: List[str] = Field(default_factory=list)
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    memberCount: int = 1
