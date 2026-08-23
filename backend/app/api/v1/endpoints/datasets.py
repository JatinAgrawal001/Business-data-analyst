from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Query
from fastapi.responses import Response
from app.core.security import get_current_user, get_supabase_user_token
from app.models.user import User
from app.schemas.dataset import Dataset, DatasetPreviewResponse, DatasetColumn
from app.schemas.profiler import ComprehensiveDatasetProfile
from app.services.dataset_service import dataset_service
from app.core.logging import get_logger

logger = get_logger("app.api.v1.datasets")
router = APIRouter(prefix="/datasets", tags=["Datasets"])

@router.get("", response_model=List[Dataset], summary="List User Datasets")
async def list_datasets(
    projectId: Optional[str] = Query(None, description="Optional project filter"),
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Lists all dataset metadata records accessible to the authenticated user.
    """
    rows = await dataset_service.list_datasets(
        user_id=current_user.id, project_id=projectId, user_jwt=user_jwt
    )
    return [
        Dataset(
            id=str(r.get("id")),
            projectId=str(r.get("project_id", "")),
            name=r.get("name", "Dataset"),
            description=r.get("description", ""),
            rowCount=r.get("row_count", 0),
            columnCount=r.get("column_count", 0),
            columns=r.get("columns") or [],
            sampleRows=r.get("sample_rows") or [],
            sizeBytes=r.get("size_bytes", 0),
            uploadedAt=r.get("uploaded_at", ""),
            fileType=r.get("file_type", "csv"),
            fileName=r.get("file_name"),
            storageBucket=r.get("storage_bucket", "datasets"),
            storagePath=r.get("storage_path"),
            status=r.get("status", "completed"),
            errorMessage=r.get("error_message"),
            processingTimeMs=r.get("processing_time_ms"),
            tags=r.get("tags") or []
        )
        for r in rows
    ]

@router.post("/upload", response_model=Dataset, status_code=status.HTTP_201_CREATED, summary="Upload & Profile Dataset (CSV, XLS, XLSX)")
async def upload_dataset(
    file: UploadFile = File(..., description="Dataset file (.csv, .xls, .xlsx only)"),
    projectId: str = Form(default="default-project", description="Target project ID"),
    name: Optional[str] = Form(default=None, description="Optional custom display name"),
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Uploads raw CSV, XLS, or XLSX file into Supabase Storage `{user_id}/{project_id}/{secure_filename}`,
    executes dynamic Pandas profiling without assuming a fixed schema, and returns dataset status.
    """
    contents = await file.read()
    original_filename = file.filename or "dataset.csv"

    dataset_obj = await dataset_service.process_and_upload_dataset(
        file_bytes=contents,
        original_filename=original_filename,
        user_id=current_user.id,
        project_id=projectId,
        custom_name=name,
        content_type=file.content_type or "text/csv",
        user_jwt=user_jwt
    )

    return dataset_obj

@router.get("/{dataset_id}", response_model=Dataset, summary="Get Dataset by ID")
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Retrieves full dataset metadata, status, error details, and inferred column profiles.
    """
    record = await dataset_service.get_dataset(dataset_id, current_user.id, user_jwt=user_jwt)
    return Dataset(
        id=str(record.get("id")),
        projectId=str(record.get("project_id", "")),
        name=record.get("name", ""),
        description=record.get("description", ""),
        rowCount=record.get("row_count", 0),
        columnCount=record.get("column_count", 0),
        columns=record.get("columns") or [],
        sampleRows=record.get("sample_rows") or [],
        sizeBytes=record.get("size_bytes", 0),
        uploadedAt=record.get("uploaded_at", ""),
        fileType=record.get("file_type", "csv"),
        fileName=record.get("file_name"),
        storageBucket=record.get("storage_bucket", "datasets"),
        storagePath=record.get("storage_path"),
        status=record.get("status", "completed"),
        errorMessage=record.get("error_message"),
        processingTimeMs=record.get("processing_time_ms"),
        tags=record.get("tags") or []
    )

@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse, summary="Get Dataset Preview & Samples")
async def get_dataset_preview(
    dataset_id: str,
    limit: int = Query(default=25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Returns preview summary and sample rows for frontend grid rendering.
    """
    return await dataset_service.get_dataset_preview(
        dataset_id=dataset_id, user_id=current_user.id, limit=limit, user_jwt=user_jwt
    )

@router.get("/{dataset_id}/profile", response_model=ComprehensiveDatasetProfile, summary="Get Deep Statistical Dataset Profile")
async def get_dataset_deep_profile(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Returns comprehensive dynamic statistical profiling: moments, quantiles, IQR outliers,
    entropy, data quality score, and Pearson/Spearman correlation matrices.
    """
    return await dataset_service.get_comprehensive_profile(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )

@router.get("/{dataset_id}/columns", response_model=List[DatasetColumn], summary="Get Column Profiles")
async def get_dataset_columns(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Returns detailed column profiles, data types, and histograms.
    """
    record = await dataset_service.get_dataset(dataset_id, current_user.id, user_jwt=user_jwt)
    return record.get("columns") or []

@router.get("/{dataset_id}/download", summary="Download Raw Dataset Binary")
async def download_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Streams raw binary dataset file directly from Supabase Storage.
    """
    file_bytes, file_name, content_type = await dataset_service.download_dataset_bytes(
        dataset_id=dataset_id, user_id=current_user.id, user_jwt=user_jwt
    )

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'}
    )

@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Dataset")
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Deletes the dataset file from Supabase Storage and deletes the record from PostgreSQL.
    """
    await dataset_service.delete_dataset(dataset_id, current_user.id, user_jwt=user_jwt)
    return None
