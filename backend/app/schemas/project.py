from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default="", max_length=500)
    tags: List[str] = Field(default_factory=list)
    status: Literal['active', 'archived', 'analyzing'] = "active"

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None
    status: Optional[Literal['active', 'archived', 'analyzing']] = None
    defaultDatasetId: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: str
    userId: Optional[str] = None
    datasetIds: List[str] = Field(default_factory=list)
    defaultDatasetId: Optional[str] = None
    memberCount: int = 1
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
