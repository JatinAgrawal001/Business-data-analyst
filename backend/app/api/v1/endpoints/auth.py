from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user, get_supabase_user_token
from app.models.user import User
from app.schemas.auth import UserProfileResponse, UserProfileUpdate
from app.services.repositories.profile_repository import profile_repository
from app.core.logging import get_logger

logger = get_logger("app.api.v1.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/me", response_model=UserProfileResponse, summary="Get Current Authenticated User")
async def get_authenticated_user_profile(
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Validates Supabase JWT and retrieves verified user profile from `public.profiles`.
    """
    db_profile = await profile_repository.get_by_user_id(current_user.id, user_jwt=user_jwt)
    if db_profile:
        return UserProfileResponse(
            id=db_profile.get("id", current_user.id),
            name=db_profile.get("name", current_user.name),
            email=db_profile.get("email", current_user.email),
            avatar=db_profile.get("avatar_url", current_user.avatar),
            role=db_profile.get("role", current_user.role),
            company=db_profile.get("company", current_user.company),
            plan=db_profile.get("plan", current_user.plan),
            createdAt=db_profile.get("created_at", current_user.createdAt),
            preferences=db_profile.get("preferences", current_user.preferences.dict())
        )

    return UserProfileResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        avatar=current_user.avatar,
        role=current_user.role,
        company=current_user.company,
        plan=current_user.plan,
        createdAt=current_user.createdAt,
        preferences=current_user.preferences
    )

@router.patch("/profile", response_model=UserProfileResponse, summary="Update User Profile")
async def update_user_profile(
    updates: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Updates the authenticated user's profile in Supabase `profiles` table.
    """
    payload = {"id": current_user.id}
    if updates.name is not None:
        payload["name"] = updates.name
    if updates.avatar is not None:
        payload["avatar_url"] = updates.avatar
    if updates.company is not None:
        payload["company"] = updates.company
    if updates.preferences is not None:
        payload["preferences"] = updates.preferences.dict()

    updated = await profile_repository.upsert_profile(payload, user_jwt=user_jwt)
    
    return UserProfileResponse(
        id=current_user.id,
        name=updated.get("name", current_user.name),
        email=current_user.email,
        avatar=updated.get("avatar_url", current_user.avatar),
        role=current_user.role,
        company=updated.get("company", current_user.company),
        plan=current_user.plan,
        createdAt=current_user.createdAt,
        preferences=updated.get("preferences", current_user.preferences.dict())
    )
