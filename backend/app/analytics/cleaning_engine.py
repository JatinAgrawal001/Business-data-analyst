import re
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from app.schemas.cleaning import CleaningRecommendation, AppliedActionDetail, TransformationResult
from app.core.logging import get_logger

logger = get_logger("app.analytics.cleaning_engine")

class DeterministicCleaningEngine:
    """
    Pure Python & Pandas deterministic data transformation execution engine.
    Executes only user-approved cleaning recipes without hallucination.
    """

    def apply_transformation(
        self,
        df: pd.DataFrame,
        recommendation: CleaningRecommendation
    ) -> Tuple[pd.DataFrame, AppliedActionDetail]:
        """
        Applies a single approved transformation deterministically on the DataFrame.
        """
        action = recommendation.action_type
        col = recommendation.column
        params = recommendation.parameters or {}
        rows_modified = 0
        desc = ""

        # 1. Missing Values Imputation & Dropping
        if action == "impute_mean" and col and col in df.columns:
            mean_val = float(df[col].mean())
            null_mask = df[col].isna()
            rows_modified = int(null_mask.sum())
            df[col] = df[col].fillna(mean_val)
            desc = f"Imputed {rows_modified} missing values in '{col}' with mean ({mean_val:.2f})"

        elif action == "impute_median" and col and col in df.columns:
            median_val = float(df[col].median())
            null_mask = df[col].isna()
            rows_modified = int(null_mask.sum())
            df[col] = df[col].fillna(median_val)
            desc = f"Imputed {rows_modified} missing values in '{col}' with median ({median_val:.2f})"

        elif action == "impute_mode" and col and col in df.columns:
            mode_series = df[col].mode()
            mode_val = mode_series.iloc[0] if len(mode_series) > 0 else "Unknown"
            null_mask = df[col].isna()
            rows_modified = int(null_mask.sum())
            df[col] = df[col].fillna(mode_val)
            desc = f"Imputed {rows_modified} missing values in '{col}' with mode ('{mode_val}')"

        elif action == "impute_constant" and col and col in df.columns:
            constant_val = params.get("value", "N/A")
            null_mask = df[col].isna()
            rows_modified = int(null_mask.sum())
            df[col] = df[col].fillna(constant_val)
            desc = f"Imputed {rows_modified} missing values in '{col}' with constant ('{constant_val}')"

        elif action == "impute_ffill" and col and col in df.columns:
            null_mask = df[col].isna()
            rows_modified = int(null_mask.sum())
            df[col] = df[col].ffill().bfill()
            desc = f"Applied forward/backward fill to {rows_modified} missing values in '{col}'"

        elif action == "drop_missing_rows" and col and col in df.columns:
            initial_count = len(df)
            df = df.dropna(subset=[col])
            rows_modified = initial_count - len(df)
            desc = f"Dropped {rows_modified} rows with missing values in '{col}'"

        elif action == "drop_column" and col and col in df.columns:
            df = df.drop(columns=[col])
            rows_modified = len(df)
            desc = f"Dropped entire column '{col}'"

        # 2. Duplicate Removal
        elif action == "drop_duplicates":
            initial_count = len(df)
            subset = params.get("subset")  # Optional subset of columns
            keep = params.get("keep", "first")
            df = df.drop_duplicates(subset=subset, keep=keep)
            rows_modified = initial_count - len(df)
            desc = f"Removed {rows_modified} duplicate rows"

        # 3. Categorical & Text Standardization
        elif action == "standardize_casing" and col and col in df.columns:
            casing = params.get("casing", "title")  # 'lower', 'upper', 'title'
            s_str = df[col].astype(str)
            if casing == "lower":
                df[col] = s_str.str.lower()
            elif casing == "upper":
                df[col] = s_str.str.upper()
            else:
                df[col] = s_str.str.title()
            rows_modified = len(df)
            desc = f"Standardized text casing in '{col}' to {casing}case"

        elif action == "strip_whitespace" and col and col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            rows_modified = len(df)
            desc = f"Stripped leading/trailing whitespaces in '{col}'"

        # 4. Type Coercion
        elif action == "cast_to_numeric" and col and col in df.columns:
            clean_s = df[col].astype(str).str.replace(r"[\$,€£%]", "", regex=True).str.replace(",", "").str.strip()
            df[col] = pd.to_numeric(clean_s, errors="coerce")
            rows_modified = len(df)
            desc = f"Parsed and coerced column '{col}' into clean numeric floats"

        elif action == "cast_to_datetime" and col and col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            rows_modified = len(df)
            desc = f"Standardized dates in '{col}' to ISO 8601 timestamps"

        # 5. Outlier Capping (Winsorization)
        elif action == "cap_outliers_iqr" and col and col in df.columns:
            lower = float(params.get("lower_bound", df[col].quantile(0.01)))
            upper = float(params.get("upper_bound", df[col].quantile(0.99)))
            outlier_mask = (df[col] < lower) | (df[col] > upper)
            rows_modified = int(outlier_mask.sum())
            df[col] = df[col].clip(lower=lower, upper=upper)
            desc = f"Capped {rows_modified} extreme outliers in '{col}' to bounds [{lower:.2f}, {upper:.2f}]"

        elif action == "remove_outliers" and col and col in df.columns:
            lower = float(params.get("lower_bound", df[col].quantile(0.01)))
            upper = float(params.get("upper_bound", df[col].quantile(0.99)))
            initial_count = len(df)
            df = df[(df[col] >= lower) & (df[col] <= upper)]
            rows_modified = initial_count - len(df)
            desc = f"Removed {rows_modified} outlier rows from '{col}'"

        # 6. Suspicious Value Replacement
        elif action == "replace_suspicious_values" and col and col in df.columns:
            target_val = params.get("target_value")
            replacement_val = params.get("replacement_value", 0.0)
            if target_val == "negative":
                mask = df[col] < 0
                rows_modified = int(mask.sum())
                df.loc[mask, col] = replacement_val
                desc = f"Replaced {rows_modified} negative values in '{col}' with {replacement_val}"
            elif target_val is not None:
                mask = df[col] == target_val
                rows_modified = int(mask.sum())
                df.loc[mask, col] = replacement_val
                desc = f"Replaced {rows_modified} occurrences of {target_val} in '{col}' with {replacement_val}"

        detail = AppliedActionDetail(
            recommendation_id=recommendation.id,
            action_type=action,
            column=col,
            description=desc or f"Applied {action} on {col}",
            rows_modified=rows_modified
        )

        return df, detail

    def execute_batch(
        self,
        df: pd.DataFrame,
        recommendations: List[CleaningRecommendation]
    ) -> Tuple[pd.DataFrame, List[AppliedActionDetail]]:
        """
        Executes an approved sequence of cleaning recommendations deterministically.
        """
        working_df = df.copy(deep=True)
        applied_details: List[AppliedActionDetail] = []

        for rec in recommendations:
            try:
                working_df, detail = self.apply_transformation(working_df, rec)
                applied_details.append(detail)
            except Exception as e:
                logger.error(f"Error applying recommendation {rec.id} ({rec.action_type}): {e}")

        return working_df, applied_details

cleaning_engine = DeterministicCleaningEngine()
