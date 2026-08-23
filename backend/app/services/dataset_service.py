import time
import uuid
import pandas as pd
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, status
from app.core.config import settings
from app.services.supabase_client import supabase_manager
from app.storage.supabase import storage_service
from app.analytics.profiler import profiler
from app.services.project_service import project_service, ensure_valid_uuid
from app.core.security import verify_resource_ownership
from app.schemas.dataset import Dataset, DatasetPreviewResponse, DatasetStatus, DatasetColumn
from app.schemas.profiler import ComprehensiveDatasetProfile
from app.core.logging import get_logger

logger = get_logger("app.services.dataset")

class DatasetService:
    """
    Complete dataset upload and dynamic profiling pipeline for CSV, XLS, and XLSX.
    """

    def __init__(self):
        self._local_datasets: Dict[str, Dict[str, Any]] = {}
        self._local_files: Dict[str, bytes] = {}

    async def list_datasets(
        self, user_id: str, project_id: Optional[str] = None, user_jwt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        client = supabase_manager.get_user_scoped_client(user_jwt)
        clean_pid = ensure_valid_uuid(project_id) if project_id else None

        if client:
            try:
                query = client.table("datasets").select("*").order("uploaded_at", desc=True)
                if clean_pid:
                    query = query.eq("project_id", clean_pid)
                res = query.execute()
                if res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Error listing datasets from Supabase: {e}")

        return [
            d for d in self._local_datasets.values()
            if d.get("user_id") == user_id and (not clean_pid or d.get("project_id") in [clean_pid, project_id])
        ]

    async def get_dataset(self, dataset_id: str, user_id: str, user_jwt: Optional[str] = None) -> Dict[str, Any]:
        clean_ds_id = ensure_valid_uuid(dataset_id)
        client = supabase_manager.get_user_scoped_client(user_jwt)
        
        if client:
            try:
                res = client.table("datasets").select("*").eq("id", clean_ds_id).maybe_single().execute()
                if res and res.data:
                    verify_resource_ownership(res.data.get("user_id"), user_id, "Dataset")
                    return res.data
            except HTTPException:
                raise
            except Exception as e:
                logger.debug(f"Dataset lookup in Supabase: {e}")

        record = self._local_datasets.get(clean_ds_id) or self._local_datasets.get(dataset_id)
        if record:
            verify_resource_ownership(record.get("user_id"), user_id, "Dataset")
            return record

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    async def process_and_upload_dataset(
        self,
        file_bytes: bytes,
        original_filename: str,
        user_id: str,
        project_id: str,
        custom_name: Optional[str] = None,
        content_type: str = "text/csv",
        user_jwt: Optional[str] = None
    ) -> Dataset:
        start_time = time.time()

        # 1. Format validation
        try:
            file_type = profiler.validate_file_format(original_filename)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(err)
            )

        # 2. Size validation
        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty. Please upload a valid CSV, XLS, or XLSX file."
            )

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        # 3. Project container validation
        clean_project_id = ensure_valid_uuid(project_id)
        try:
            await project_service.get_project(clean_project_id, user_id, user_jwt)
        except HTTPException:
            await project_service.create_project(
                user_id=user_id,
                payload={"id": clean_project_id, "name": f"Project {project_id[:8]}"},
                user_jwt=user_jwt
            )

        dataset_id = str(uuid.uuid4())
        dataset_name = custom_name or original_filename.rsplit(".", 1)[0]

        # 4. Store file in Supabase Storage
        storage_info = await storage_service.upload_file(
            file_bytes=file_bytes,
            original_filename=original_filename,
            user_id=user_id,
            project_id=clean_project_id,
            content_type=content_type,
            user_jwt=user_jwt
        )

        self._local_files[storage_info["storagePath"]] = file_bytes
        self._local_files[dataset_id] = file_bytes

        # 5. Dynamic Profiling (zero schema assumptions)
        status_state: DatasetStatus = "completed"
        error_msg: Optional[str] = None

        try:
            df = profiler.parse_file_to_dataframe(file_bytes, file_type)
            if df.empty:
                raise ValueError("Dataset contains no rows or data entries.")
        except Exception as e:
            status_state = "failed"
            error_msg = str(e)
            logger.error(f"Dataset processing error on {dataset_id}: {e}")

            failed_dataset = Dataset(
                id=dataset_id,
                projectId=clean_project_id,
                name=dataset_name,
                description=f"Processing failed: {original_filename}",
                rowCount=0,
                columnCount=0,
                columns=[],
                sampleRows=[],
                sizeBytes=len(file_bytes),
                fileType=file_type,
                fileName=storage_info["fileName"],
                storageBucket=storage_info["storageBucket"],
                storagePath=storage_info["storagePath"],
                status=status_state,
                errorMessage=error_msg,
                processingTimeMs=round((time.time() - start_time) * 1000, 2)
            )
            self._local_datasets[dataset_id] = failed_dataset.model_dump()
            return failed_dataset

        processing_duration_ms = round((time.time() - start_time) * 1000, 2)

        dataset_obj = profiler.profile_dataframe(
            df=df,
            dataset_id=dataset_id,
            project_id=clean_project_id,
            name=dataset_name,
            original_filename=storage_info["fileName"],
            file_type=file_type,
            storage_bucket=storage_info["storageBucket"],
            storage_path=storage_info["storagePath"],
            status=status_state,
            processing_time_ms=processing_duration_ms
        )

        payload = {
            "id": dataset_obj.id,
            "user_id": user_id,
            "project_id": clean_project_id,
            "name": dataset_obj.name,
            "description": dataset_obj.description,
            "file_name": dataset_obj.fileName,
            "file_type": dataset_obj.fileType,
            "storage_bucket": dataset_obj.storageBucket,
            "storage_path": dataset_obj.storagePath,
            "row_count": dataset_obj.rowCount,
            "column_count": dataset_obj.columnCount,
            "columns": [c.model_dump() for c in dataset_obj.columns],
            "sample_rows": dataset_obj.sampleRows,
            "size_bytes": dataset_obj.sizeBytes,
            "status": dataset_obj.status,
            "tags": dataset_obj.tags,
            "processing_time_ms": processing_duration_ms
        }

        self._local_datasets[dataset_id] = payload

        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                client.table("datasets").insert(payload).execute()
            except Exception as e:
                logger.debug(f"Supabase DB insert note: {e}")

        return dataset_obj

    async def get_dataset_preview(
        self, dataset_id: str, user_id: str, limit: int = 50, user_jwt: Optional[str] = None
    ) -> DatasetPreviewResponse:
        record = await self.get_dataset(dataset_id, user_id, user_jwt)
        raw_columns = record.get("columns") or []
        columns = [
            c if isinstance(c, DatasetColumn) else DatasetColumn(**c) for c in raw_columns
        ]

        return DatasetPreviewResponse(
            id=str(record.get("id")),
            projectId=str(record.get("project_id", "")),
            name=str(record.get("name", "")),
            status=record.get("status", "completed"),
            rowCount=record.get("row_count", 0),
            columnCount=record.get("column_count", 0),
            columns=columns,
            sampleRows=(record.get("sample_rows") or [])[:limit],
            fileType=record.get("file_type", "csv"),
            storagePath=record.get("storage_path"),
            errorMessage=record.get("error_message"),
            processingTimeMs=record.get("processing_time_ms")
        )

    async def get_comprehensive_profile(
        self, dataset_id: str, user_id: str, user_jwt: Optional[str] = None
    ) -> ComprehensiveDatasetProfile:
        """
        Executes deep dynamic statistical profiling, correlations, and quality audit.
        """
        record = await self.get_dataset(dataset_id, user_id, user_jwt)
        file_bytes, file_name, _ = await self.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)

        return profiler.generate_comprehensive_profile(
            df=df,
            dataset_id=dataset_id,
            project_id=str(record.get("project_id", "")),
            name=str(record.get("name", "")),
            file_type=file_type
        )

    async def download_dataset_bytes(
        self, dataset_id: str, user_id: str, user_jwt: Optional[str] = None
    ) -> Tuple[bytes, str, str]:
        record = await self.get_dataset(dataset_id, user_id, user_jwt)
        storage_path = record.get("storage_path")
        
        file_bytes = None
        if storage_path:
            file_bytes = await storage_service.download_file(storage_path, user_jwt=user_jwt)
            if not file_bytes:
                file_bytes = self._local_files.get(storage_path)
        
        if not file_bytes:
            file_bytes = self._local_files.get(dataset_id)

        if not file_bytes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File bytes not found in storage")

        file_name = record.get("file_name") or f"dataset_{dataset_id}.csv"
        ext = file_name.split(".")[-1].lower()
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if "xls" in ext else "text/csv"

        return file_bytes, file_name, content_type

    async def delete_dataset(self, dataset_id: str, user_id: str, user_jwt: Optional[str] = None) -> bool:
        record = await self.get_dataset(dataset_id, user_id, user_jwt)
        clean_ds_id = record["id"]

        if record.get("storage_path"):
            await storage_service.delete_file(record["storage_path"], user_jwt=user_jwt)
            self._local_files.pop(record["storage_path"], None)

        self._local_files.pop(clean_ds_id, None)
        self._local_files.pop(dataset_id, None)

        client = supabase_manager.get_user_scoped_client(user_jwt)
        if client:
            try:
                client.table("datasets").delete().eq("id", clean_ds_id).execute()
            except Exception as e:
                logger.debug(f"Supabase dataset delete note: {e}")

        self._local_datasets.pop(clean_ds_id, None)
        return True

dataset_service = DatasetService()
