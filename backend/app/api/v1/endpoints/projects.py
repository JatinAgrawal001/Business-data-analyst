import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user, get_supabase_user_token
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.repositories.project_repository import project_repository

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectResponse], summary="List User Projects")
async def list_projects(
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Lists projects owned by the authenticated user with RLS scoping.
    """
    rows = await project_repository.list_for_user(user_id=current_user.id, user_jwt=user_jwt)
    return [
        ProjectResponse(
            id=str(r.get("id")),
            userId=str(r.get("user_id", current_user.id)),
            name=r.get("name", "Untitled Project"),
            description=r.get("description", ""),
            tags=r.get("tags") or [],
            status=r.get("status", "active"),
            datasetIds=r.get("dataset_ids") or [],
            defaultDatasetId=str(r.get("default_dataset_id")) if r.get("default_dataset_id") else None,
            memberCount=r.get("member_count", 1),
            createdAt=r.get("created_at", ""),
            updatedAt=r.get("updated_at", "")
        )
        for r in rows
    ]

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create Project")
async def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Creates a new project container associated with the authenticated user.
    """
    proj_id = str(uuid.uuid4())
    payload = {
        "id": proj_id,
        "user_id": current_user.id,
        "name": project_in.name,
        "description": project_in.description,
        "tags": project_in.tags,
        "status": project_in.status,
        "member_count": 1
    }

    created = await project_repository.create(payload, user_jwt=user_jwt)
    return ProjectResponse(
        id=str(created.get("id", proj_id)),
        userId=current_user.id,
        name=created.get("name", project_in.name),
        description=created.get("description", project_in.description),
        tags=created.get("tags", project_in.tags),
        status=created.get("status", project_in.status),
        datasetIds=created.get("dataset_ids", []),
        memberCount=created.get("member_count", 1),
        createdAt=created.get("created_at", ""),
        updatedAt=created.get("updated_at", "")
    )

@router.get("/{project_id}", response_model=ProjectResponse, summary="Get Project by ID")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Retrieves project by ID ensuring user ownership via RLS.
    """
    row = await project_repository.get_by_id(project_id, user_jwt=user_jwt)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return ProjectResponse(
        id=str(row.get("id")),
        userId=str(row.get("user_id")),
        name=row.get("name"),
        description=row.get("description", ""),
        tags=row.get("tags") or [],
        status=row.get("status", "active"),
        datasetIds=row.get("dataset_ids") or [],
        defaultDatasetId=str(row.get("default_dataset_id")) if row.get("default_dataset_id") else None,
        memberCount=row.get("member_count", 1),
        createdAt=row.get("created_at", ""),
        updatedAt=row.get("updated_at", "")
    )

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Project")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Deletes a project record.
    """
    success = await project_repository.delete(project_id, user_jwt=user_jwt)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete project")
    return None
