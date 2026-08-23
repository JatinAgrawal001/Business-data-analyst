import uuid
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from app.services.dataset_service import dataset_service
from app.analytics.profiler import profiler
from app.analytics.cleaning_engine import cleaning_engine
from app.agents.data_cleaning_agent import data_cleaning_agent
from app.schemas.cleaning import (
    CleaningRecommendation,
    CleaningAuditReport,
    ApplyTransformationsRequest,
    TransformationResult
)
from app.core.logging import get_logger

logger = get_logger("app.services.cleaning")

class DataCleaningService:
    """
    Coordinates Data Cleaning Agent audits, recommendation storage,
    and user-approved transformation executions.
    """

    def __init__(self):
        # Cache recommendations: dataset_id -> Dict[recommendation_id, CleaningRecommendation]
        self._recommendations_cache: Dict[str, Dict[str, CleaningRecommendation]] = {}

    async def audit_dataset(
        self,
        dataset_id: str,
        user_id: str,
        user_jwt: Optional[str] = None
    ) -> CleaningAuditReport:
        """
        Runs the Data Cleaning Agent to audit the dataset and produce recommendations.
        Does NOT modify user data.
        """
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile = profiler.generate_comprehensive_profile(df, dataset_id, "default-project", file_name, file_type)

        audit_report = data_cleaning_agent.analyze_and_recommend(df, profile)

        self._recommendations_cache[dataset_id] = {
            rec.id: rec for rec in audit_report.recommendations
        }

        return audit_report

    async def get_recommendations(
        self,
        dataset_id: str,
        user_id: str,
        user_jwt: Optional[str] = None
    ) -> List[CleaningRecommendation]:
        """
        Retrieves active recommendations for a dataset. If not cached, runs audit.
        """
        if dataset_id not in self._recommendations_cache:
            report = await self.audit_dataset(dataset_id, user_id, user_jwt)
            return report.recommendations

        return list(self._recommendations_cache[dataset_id].values())

    async def apply_transformations(
        self,
        dataset_id: str,
        user_id: str,
        request: ApplyTransformationsRequest,
        user_jwt: Optional[str] = None
    ) -> TransformationResult:
        """
        Executes approved transformations deterministically on the dataset using Python/Pandas.
        """
        cached = self._recommendations_cache.get(dataset_id)
        if not cached:
            await self.audit_dataset(dataset_id, user_id, user_jwt)
            cached = self._recommendations_cache.get(dataset_id, {})

        approved_recs: List[CleaningRecommendation] = [
            cached[rec_id] for rec_id in request.approved_recommendation_ids
            if rec_id in cached
        ]

        if not approved_recs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No matching approved recommendations found for this dataset."
            )

        # 1. Load DataFrame & Profile before
        file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, user_id, user_jwt)
        file_type = profiler.validate_file_format(file_name)
        df_before = profiler.parse_file_to_dataframe(file_bytes, file_type)
        profile_before = profiler.generate_comprehensive_profile(df_before, dataset_id, "default-project", file_name, file_type)

        # 2. Execute approved transformations deterministically
        cleaned_df, applied_details = cleaning_engine.execute_batch(df_before, approved_recs)

        # 3. Profile after
        profile_after = profiler.generate_comprehensive_profile(cleaned_df, dataset_id, "default-project", file_name, file_type)

        # 4. Convert back to CSV bytes and persist
        io_bytes = cleaned_df.to_csv(index=False).encode("utf-8")

        target_dataset_id = dataset_id
        if request.save_as_new_dataset:
            new_name = request.new_dataset_name or f"Cleaned_{file_name}"
            new_dataset_obj = await dataset_service.process_and_upload_dataset(
                file_bytes=io_bytes,
                original_filename=f"cleaned_{file_name}",
                user_id=user_id,
                project_id=profile_before.project_id,
                custom_name=new_name,
                user_jwt=user_jwt
            )
            target_dataset_id = new_dataset_obj.id
        else:
            dataset_service._local_files[dataset_id] = io_bytes
            updated_dataset_obj = profiler.profile_dataframe(
                df=cleaned_df,
                dataset_id=dataset_id,
                project_id=profile_before.project_id,
                name=profile_before.name,
                original_filename=file_name,
                file_type=file_type,
                status="completed"
            )
            dataset_service._local_datasets[dataset_id] = updated_dataset_obj.model_dump()

        for rec in approved_recs:
            rec.status = "approved"

        clean_sample_df = cleaned_df.head(25).replace({np.nan: None})
        sample_rows = clean_sample_df.to_dict(orient="records")

        for row in sample_rows:
            for k, v in row.items():
                if isinstance(v, (pd.Timestamp, np.datetime64)):
                    row[k] = str(v)

        return TransformationResult(
            dataset_id=target_dataset_id,
            actions_applied_count=len(applied_details),
            rows_before=len(df_before),
            rows_after=len(cleaned_df),
            columns_before=len(df_before.columns),
            columns_after=len(cleaned_df.columns),
            health_score_before=profile_before.quality_report.health_score,
            health_score_after=profile_after.quality_report.health_score,
            applied_actions=applied_details,
            preview_rows=sample_rows
        )

cleaning_service = DataCleaningService()
