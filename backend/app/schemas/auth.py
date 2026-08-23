from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from app.models.user import UserPreferences

class UserProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    avatar: Optional[str] = None
    role: str = "Lead Business Data Analyst"
    company: str = "Enterprise Workspace"
    plan: Literal['Starter', 'Professional', 'Enterprise'] = "Enterprise"
    createdAt: str
    preferences: UserPreferences = Field(default_factory=UserPreferences)

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    company: Optional[str] = None
    preferences: Optional[UserPreferences] = None
