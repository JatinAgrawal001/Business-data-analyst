import uuid
import re
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from google.adk.agents import Agent
from app.schemas.profiler import DatasetProfile
from app.schemas.cleaning import CleaningRecommendation, CleaningAuditReport
from app.core.logging import get_logger

logger = get_logger("app.agents.data_cleaning")

class DataCleaningAgent:
    """
    Google ADK-powered Data Cleaning & Anomaly Detection Agent.
    Audits DatasetProfile and raw DataFrame to detect:
    - missing values
    - duplicate rows
    - incorrect types
    - inconsistent categorical values
    - suspicious values
    - possible outliers
    
    Returns structured recommendations for user approval without mutating user data automatically.
    """

    def __init__(self):
        self._setup_adk_agent()

    def _setup_adk_agent(self):
        """Initializes the Google ADK Agent instance."""
        try:
            self.adk_agent = Agent(
                name="data_cleaning_agent",
                model="gemini-2.5-flash",
                instruction=(
                    "You are an expert Data Cleaning Agent. Analyze the DatasetProfile for anomalies, "
                    "missing values, duplicate rows, incorrect types, inconsistent casing, suspicious negative values, "
                    "and extreme outliers. Generate structured, actionable cleaning recommendations with clear statistical justifications. "
                    "Do NOT mutate data automatically."
                ),
                description="Audits datasets and generates actionable data cleaning recommendations."
            )
        except Exception as e:
            logger.warning(f"ADK Agent initialization notice: {e}")
            self.adk_agent = None

    def analyze_and_recommend(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile
    ) -> CleaningAuditReport:
        """
        Comprehensive audit analyzing DatasetProfile and DataFrame.
        Produces structured recommendations for user review.
        """
        recommendations: List[CleaningRecommendation] = []
        total_rows = len(df)
        if total_rows == 0:
            return CleaningAuditReport(dataset_id=profile.dataset_id, total_issues_found=0, health_score_before=100.0, recommendations=[])

        # =========================================================================
        # 1. Duplicate Rows Detection
        # =========================================================================
        exact_dups = int(df.duplicated().sum())
        if exact_dups > 0:
            dup_pct = round((exact_dups / total_rows) * 100, 2)
            recommendations.append(CleaningRecommendation(
                id=str(uuid.uuid4()),
                issue="duplicate_rows",
                column=None,
                affected_rows=exact_dups,
                affected_percentage=dup_pct,
                suggested_action=f"Remove {exact_dups} duplicate rows (keep first occurrence)",
                action_type="drop_duplicates",
                reason=f"Found {exact_dups} ({dup_pct}%) duplicate rows which cause skewed metric totals.",
                parameters={"keep": "first"},
                status="pending"
            ))

        # =========================================================================
        # 2. Missing Values Detection & Strategy Recommendation
        # =========================================================================
        for col_profile in profile.columns:
            col_name = col_profile.name
            null_count = col_profile.null_count
            null_pct = col_profile.null_percentage

            if null_count > 0:
                if null_pct > 60.0:
                    recommendations.append(CleaningRecommendation(
                        id=str(uuid.uuid4()),
                        issue="missing_values",
                        column=col_name,
                        affected_rows=null_count,
                        affected_percentage=null_pct,
                        suggested_action=f"Drop column '{col_name}' ({null_pct:.1f}% missing values)",
                        action_type="drop_column",
                        reason=f"Column '{col_name}' has over 60% missing data ({null_count}/{total_rows} rows).",
                        parameters={"column": col_name},
                        status="pending"
                    ))
                elif col_profile.data_type == "numeric":
                    num_stats = col_profile.numeric_stats
                    if num_stats and abs(num_stats.skewness) > 1.0:
                        recommendations.append(CleaningRecommendation(
                            id=str(uuid.uuid4()),
                            issue="missing_values",
                            column=col_name,
                            affected_rows=null_count,
                            affected_percentage=null_pct,
                            suggested_action=f"Impute missing values in '{col_name}' with median ({num_stats.median:.2f})",
                            action_type="impute_median",
                            reason=f"Column '{col_name}' is skewed (skewness = {num_stats.skewness:.2f}). Median imputation is robust against outlier distortion.",
                            parameters={"value": num_stats.median},
                            status="pending"
                        ))
                    elif num_stats:
                        recommendations.append(CleaningRecommendation(
                            id=str(uuid.uuid4()),
                            issue="missing_values",
                            column=col_name,
                            affected_rows=null_count,
                            affected_percentage=null_pct,
                            suggested_action=f"Impute missing values in '{col_name}' with mean ({num_stats.mean:.2f})",
                            action_type="impute_mean",
                            reason=f"Column '{col_name}' has symmetric distribution (skewness = {num_stats.skewness:.2f}). Mean preserves central tendency.",
                            parameters={"value": num_stats.mean},
                            status="pending"
                        ))
                elif col_profile.data_type in ["categorical", "text"]:
                    cat_stats = col_profile.categorical_stats
                    mode_val = cat_stats.mode if cat_stats and cat_stats.mode else "Unknown"
                    recommendations.append(CleaningRecommendation(
                        id=str(uuid.uuid4()),
                        issue="missing_values",
                        column=col_name,
                        affected_rows=null_count,
                        affected_percentage=null_pct,
                        suggested_action=f"Impute missing values in '{col_name}' with mode ('{mode_val}')",
                        action_type="impute_mode",
                        reason=f"Categorical column '{col_name}' missing in {null_count} rows. Imputing with most frequent category ('{mode_val}').",
                        parameters={"value": mode_val},
                        status="pending"
                    ))
                elif col_profile.data_type == "datetime":
                    recommendations.append(CleaningRecommendation(
                        id=str(uuid.uuid4()),
                        issue="missing_values",
                        column=col_name,
                        affected_rows=null_count,
                        affected_percentage=null_pct,
                        suggested_action=f"Forward-fill missing dates in '{col_name}'",
                        action_type="impute_ffill",
                        reason=f"Time-series datetime column '{col_name}' has missing entries. Forward-fill preserves temporal continuity.",
                        parameters={},
                        status="pending"
                    ))

        # =========================================================================
        # 3. Incorrect Types & Formatted Numeric String Detection
        # =========================================================================
        for col_name in df.columns:
            s = df[col_name]
            if not pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_datetime64_any_dtype(s):
                non_nulls = s.dropna().astype(str)
                if len(non_nulls) > 0:
                    sample_strs = non_nulls.head(50).tolist()
                    formatted_matches = sum(
                        bool(re.search(r"[\$,€£%]", val)) or bool(re.match(r"^\s*[\$,€£]?\s*[-+]?[0-9]{1,3}(,[0-9]{3})*(\.[0-9]+)?\s*[%]?\s*$", val))
                        for val in sample_strs
                    )
                    if formatted_matches / len(sample_strs) >= 0.5:
                        recommendations.append(CleaningRecommendation(
                            id=str(uuid.uuid4()),
                            issue="incorrect_types",
                            column=col_name,
                            affected_rows=len(non_nulls),
                            affected_percentage=round((len(non_nulls) / total_rows) * 100, 2),
                            suggested_action=f"Coerce formatted text in '{col_name}' into numeric floats",
                            action_type="cast_to_numeric",
                            reason=f"Column '{col_name}' is stored as string/object but contains numeric values with symbols/formatting ($/€/%/,).",
                            parameters={},
                            status="pending"
                        ))

        # =========================================================================
        # 4. Inconsistent Categorical Values (Casing & Whitespace)
        # =========================================================================
        for col_name in df.columns:
            s = df[col_name]
            if not pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_datetime64_any_dtype(s):
                raw_values = s.dropna().astype(str).unique()
                lower_values = set(v.lower().strip() for v in raw_values)

                if len(lower_values) < len(raw_values) and len(raw_values) > 1:
                    diff_count = len(raw_values) - len(lower_values)
                    recommendations.append(CleaningRecommendation(
                        id=str(uuid.uuid4()),
                        issue="inconsistent_categories",
                        column=col_name,
                        affected_rows=total_rows,
                        affected_percentage=100.0,
                        suggested_action=f"Standardize text casing and strip whitespace in '{col_name}'",
                        action_type="standardize_casing",
                        reason=f"Found {diff_count} redundant category variants in '{col_name}' due to inconsistent capitalization or trailing spaces.",
                        parameters={"casing": "title"},
                        status="pending"
                    ))

        # =========================================================================
        # 5. Suspicious Values (Negative values in non-negative domain metrics)
        # =========================================================================
        for col_profile in profile.columns:
            if col_profile.data_type == "numeric" and col_profile.numeric_stats:
                col_name = col_profile.name
                num_stats = col_profile.numeric_stats
                name_lower = col_name.lower()

                is_strictly_positive = any(k in name_lower for k in [
                    "price", "cost", "revenue", "sales", "spend", "units", "quantity",
                    "count", "age", "salary", "discount", "distance", "duration", "clicks", "impressions"
                ])

                if is_strictly_positive and num_stats.negatives_count > 0:
                    recommendations.append(CleaningRecommendation(
                        id=str(uuid.uuid4()),
                        issue="suspicious_values",
                        column=col_name,
                        affected_rows=num_stats.negatives_count,
                        affected_percentage=round((num_stats.negatives_count / total_rows) * 100, 2),
                        suggested_action=f"Replace {num_stats.negatives_count} suspicious negative values in '{col_name}' with 0.0",
                        action_type="replace_suspicious_values",
                        reason=f"Column '{col_name}' represents a strictly positive business quantity, but contains {num_stats.negatives_count} negative entries.",
                        parameters={"target_value": "negative", "replacement_value": 0.0},
                        status="pending"
                    ))

        # =========================================================================
        # 6. Possible Outliers Detection (Tukey's IQR Fences)
        # =========================================================================
        for col_profile in profile.columns:
            if col_profile.data_type == "numeric" and col_profile.numeric_stats:
                col_name = col_profile.name
                outliers = col_profile.numeric_stats.outliers

                if outliers and outliers.outlier_count > 0 and outliers.outlier_percentage <= 15.0:
                    recommendations.append(CleaningRecommendation(
                        id=str(uuid.uuid4()),
                        issue="possible_outliers",
                        column=col_name,
                        affected_rows=outliers.outlier_count,
                        affected_percentage=outliers.outlier_percentage,
                        suggested_action=f"Cap extreme outliers in '{col_name}' to IQR bounds [{outliers.iqr_lower_bound:.2f}, {outliers.iqr_upper_bound:.2f}]",
                        action_type="cap_outliers_iqr",
                        reason=f"Detected {outliers.outlier_count} extreme outlier values beyond 1.5x IQR ({outliers.iqr_lower_bound:.2f} to {outliers.iqr_upper_bound:.2f}). Capping prevents skew in regression and aggregate metrics.",
                        parameters={
                            "lower_bound": outliers.iqr_lower_bound,
                            "upper_bound": outliers.iqr_upper_bound
                        },
                        status="pending"
                    ))

        return CleaningAuditReport(
            dataset_id=profile.dataset_id,
            total_issues_found=len(recommendations),
            health_score_before=profile.quality_report.health_score,
            recommendations=recommendations
        )

data_cleaning_agent = DataCleaningAgent()
