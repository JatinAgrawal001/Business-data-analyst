import io
import time
import math
import re
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from app.schemas.dataset import (
    Dataset,
    DatasetColumn,
    DatasetColumnSummary,
    CategoryCount,
    HistogramBucket as SimpleHistogramBucket,
    ColumnDataType,
    FileType,
    DatasetStatus
)
from app.schemas.profiler import (
    DatasetProfile,
    ColumnDetailedProfile,
    NumericStats,
    CategoricalStats,
    DatetimeStats,
    TextStats,
    PotentialMetric,
    MissingValuesSummary,
    DuplicateSummary,
    DataQualityReport,
    QualityWarning,
    CorrelationPair,
    QuantilesSummary,
    OutlierSummary,
    HistogramBucket,
    CategoryFrequency
)
from app.core.logging import get_logger

logger = get_logger("app.analytics.profiler")

class DynamicDatasetProfiler:
    """
    Deterministic Dynamic Dataset Profiler using Pandas and NumPy.
    Works with arbitrary business datasets without fixed column names.
    Calculates all statistical metrics, quantiles, distributions, outliers,
    identifier detection, and potential KPI metrics deterministically without LLM calls.
    """

    SUPPORTED_EXTENSIONS = {"csv", "xls", "xlsx"}

    def validate_file_format(self, original_filename: str) -> FileType:
        """
        Validates that the file has a supported format (.csv, .xls, .xlsx).
        """
        if not original_filename or "." not in original_filename:
            raise ValueError("File must have an extension (.csv, .xls, or .xlsx)")

        ext = original_filename.rsplit(".", 1)[-1].lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format '.{ext}'. Only CSV, XLS, and XLSX are supported.")

        return ext  # type: ignore

    def parse_file_to_dataframe(self, file_bytes: bytes, file_type: FileType) -> pd.DataFrame:
        """
        Parses raw bytes into a Pandas DataFrame without assuming any column names or structures.
        """
        try:
            if file_type == "csv":
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes))
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")
            elif file_type in ["xlsx", "xls"]:
                df = pd.read_excel(io.BytesIO(file_bytes))
            else:
                raise ValueError(f"Unsupported format {file_type}")

            return df
        except Exception as e:
            logger.error(f"Error parsing {file_type} data: {e}")
            raise ValueError(f"Corrupted or invalid {file_type.upper()} file: {str(e)}")

    def is_identifier_column(self, series: pd.Series, col_name: str, total_rows: int) -> bool:
        """
        Deterministic identifier detection independent of hardcoded domain column names:
        1. Explicit ID keywords in name (_id, id, guid, uuid, key, pk, fk, code, sku, ssn, txn_hash)
        2. High-cardinality non-datetime, non-numeric strings with token/hash formatting.
        """
        name_lower = str(col_name).lower().strip()
        non_nulls = series.dropna()
        if len(non_nulls) == 0:
            return False

        # Name-based heuristic
        clean_name = name_lower.replace(" ", "").replace("_", "").replace("-", "")
        if (
            clean_name.endswith("id")
            or clean_name.startswith("id")
            or "uuid" in clean_name
            or "guid" in clean_name
            or "hash" in clean_name
            or "rownumber" in clean_name
            or "rowid" in clean_name
            or "recordid" in clean_name
            or "accountid" in clean_name
            or "customerid" in clean_name
            or "userid" in clean_name
            or "orderid" in clean_name
            or "productid" in clean_name
            or "policyid" in clean_name
            or "matriculation" in clean_name
            or clean_name in ["id", "uuid", "guid", "key", "pk", "fk", "code", "sku", "ssn", "txn_hash", "token", "index"]
            or "identifier" in clean_name
        ):
            return True

        # Pure string token patterns with 100% uniqueness
        if not pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_datetime64_any_dtype(series):
            unique_cnt = int(non_nulls.nunique())
            if unique_cnt == len(non_nulls) and total_rows >= 10:
                sample_str = str(non_nulls.iloc[0])
                # Check if it has an ID prefix like ABC-123 or hex hash
                if re.match(r"^[A-Za-z0-9\-_]{5,}$", sample_str) and not sample_str.isalpha():
                    return True

        return False

    def is_datetime_series(self, series: pd.Series) -> bool:
        """Checks if a series contains valid datetime values."""
        if pd.api.types.is_datetime64_any_dtype(series):
            return True

        non_nulls = series.dropna()
        if len(non_nulls) == 0 or pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
            return False

        sample_strs = non_nulls.astype(str).head(30)
        date_matches = 0
        for val in sample_strs:
            if any(char in val for char in ["-", "/", "T", ":"]) and len(val) >= 6:
                try:
                    pd.to_datetime(val)
                    date_matches += 1
                except (ValueError, TypeError):
                    pass
        return len(sample_strs) > 0 and (date_matches / len(sample_strs)) >= 0.7

    def infer_column_type(self, series: pd.Series, col_name: str, total_rows: int) -> Tuple[ColumnDataType, float]:
        """
        Heuristic classification of column type and confidence score without fixed column names.
        Order: ID name checks -> Datetime -> Numeric -> Boolean -> ID format -> Categorical -> Text
        """
        non_nulls = series.dropna()
        if len(non_nulls) == 0:
            return "text", 0.50

        # 1. Identifier check (Name & token patterns)
        if self.is_identifier_column(series, col_name, total_rows):
            return "id", 0.98

        # 2. Datetime check
        if self.is_datetime_series(series):
            return "datetime", 0.95

        # 3. Boolean check
        if pd.api.types.is_bool_dtype(series) or (pd.api.types.is_numeric_dtype(series) and set(non_nulls.unique()).issubset({0, 1})):
            return "boolean", 0.99

        # 4. Numeric check
        if pd.api.types.is_numeric_dtype(series):
            return "numeric", 0.99

        # 5. Categorical check
        unique_count = series.nunique()
        total_count = len(non_nulls)
        if total_count > 0 and (unique_count <= 35 or (unique_count / total_count < 0.25)):
            return "categorical", 0.90

        # 6. Text fallback
        return "text", 0.80

    def compute_numeric_stats(self, series: pd.Series) -> Optional[NumericStats]:
        """
        Deterministic descriptive statistics, moments, quantiles, and IQR outlier boundaries using NumPy/Pandas.
        """
        clean_num = pd.to_numeric(series.dropna(), errors="coerce").dropna()
        if len(clean_num) == 0:
            return None

        arr = clean_num.values
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))
        sum_val = float(np.sum(arr))
        mean_val = float(np.mean(arr))
        median_val = float(np.median(arr))
        std_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        var_val = float(np.var(arr, ddof=1)) if len(arr) > 1 else 0.0

        # Skewness & Kurtosis
        skew_val = float(clean_num.skew()) if len(arr) >= 3 else 0.0
        kurt_val = float(clean_num.kurtosis()) if len(arr) >= 4 else 0.0
        skew_val = 0.0 if math.isnan(skew_val) else skew_val
        kurt_val = 0.0 if math.isnan(kurt_val) else kurt_val

        # Quantiles & Percentiles
        p5 = float(np.percentile(arr, 5))
        p25 = float(np.percentile(arr, 25))
        p50 = median_val
        p75 = float(np.percentile(arr, 75))
        p95 = float(np.percentile(arr, 95))
        iqr = float(p75 - p25)

        # IQR Outlier Detection (Tukey's Fences: Q1 - 1.5*IQR to Q3 + 1.5*IQR)
        iqr_lower = p25 - 1.5 * iqr
        iqr_upper = p75 + 1.5 * iqr
        outlier_mask = (arr < iqr_lower) | (arr > iqr_upper)
        outliers_arr = arr[outlier_mask]
        outlier_count = int(len(outliers_arr))
        outlier_pct = round((outlier_count / len(arr)) * 100, 2)
        outlier_samples = [float(x) for x in outliers_arr[:10]]

        # Zeros and Negatives
        zeros_cnt = int(np.sum(arr == 0))
        zeros_pct = round((zeros_cnt / len(arr)) * 100, 2)
        negatives_cnt = int(np.sum(arr < 0))

        # Adaptive Distribution Histogram (5 dynamic buckets)
        distribution = []
        if max_val > min_val:
            bins = np.linspace(min_val, max_val, 6)
            counts, _ = np.histogram(arr, bins=bins)
            for i in range(len(counts)):
                b_label = f"{bins[i]:.2f} - {bins[i+1]:.2f}"
                pct = round((counts[i] / len(arr)) * 100, 1)
                distribution.append(HistogramBucket(bucket=b_label, count=int(counts[i]), percentage=pct))
        else:
            distribution.append(HistogramBucket(bucket=f"{min_val:.2f}", count=len(arr), percentage=100.0))

        return NumericStats(
            min=round(min_val, 4),
            max=round(max_val, 4),
            mean=round(mean_val, 4),
            median=round(median_val, 4),
            std_dev=round(std_val, 4),
            variance=round(var_val, 4),
            sum=round(sum_val, 4),
            skewness=round(skew_val, 4),
            kurtosis=round(kurt_val, 4),
            zeros_count=zeros_cnt,
            zeros_percentage=zeros_pct,
            negatives_count=negatives_cnt,
            quantiles=QuantilesSummary(
                p5=round(p5, 2),
                p25=round(p25, 2),
                p50=round(p50, 2),
                p75=round(p75, 2),
                p95=round(p95, 2),
                iqr=round(iqr, 2)
            ),
            outliers=OutlierSummary(
                iqr_lower_bound=round(iqr_lower, 2),
                iqr_upper_bound=round(iqr_upper, 2),
                outlier_count=outlier_count,
                outlier_percentage=outlier_pct,
                outlier_samples=outlier_samples
            ),
            distribution=distribution
        )

    def compute_categorical_stats(self, series: pd.Series) -> CategoricalStats:
        """
        Computes cardinality, frequencies, mode, and Shannon entropy.
        """
        non_nulls = series.dropna().astype(str)
        total_cnt = len(non_nulls)
        if total_cnt == 0:
            return CategoricalStats(cardinality=0, distinct_ratio=0.0, entropy=0.0)

        val_counts = non_nulls.value_counts()
        cardinality = len(val_counts)
        distinct_ratio = round(cardinality / total_cnt, 4)
        mode_val = str(val_counts.index[0]) if cardinality > 0 else None

        probabilities = val_counts.values / total_cnt
        entropy = -float(np.sum(probabilities * np.log2(probabilities + 1e-12)))

        top_cats = []
        running_cum = 0.0
        for label, cnt in val_counts.head(10).items():
            pct = round((cnt / total_cnt) * 100, 2)
            running_cum = round(running_cum + pct, 2)
            top_cats.append(CategoryFrequency(
                label=str(label),
                count=int(cnt),
                percentage=pct,
                cumulative_percentage=min(100.0, running_cum)
            ))

        return CategoricalStats(
            cardinality=cardinality,
            distinct_ratio=distinct_ratio,
            mode=mode_val,
            entropy=round(entropy, 3),
            top_categories=top_cats
        )

    def compute_datetime_stats(self, series: pd.Series) -> Optional[DatetimeStats]:
        """
        Computes temporal span, boundaries, and detected frequency.
        """
        clean_dates = pd.to_datetime(series.dropna(), errors="coerce").dropna()
        if len(clean_dates) == 0:
            return None

        min_dt = clean_dates.min()
        max_dt = clean_dates.max()
        span_days = round((max_dt - min_dt).total_seconds() / 86400.0, 2)

        freq = None
        if len(clean_dates) > 3:
            inferred = pd.infer_freq(clean_dates.sort_values())
            freq = inferred or "Irregular / Mixed"

        return DatetimeStats(
            min_date=min_dt.isoformat(),
            max_date=max_dt.isoformat(),
            timespan_days=span_days,
            detected_frequency=freq
        )

    def compute_text_stats(self, series: pd.Series) -> TextStats:
        """
        Computes character length bounds and uniqueness metrics.
        """
        non_nulls = series.dropna().astype(str)
        if len(non_nulls) == 0:
            return TextStats(min_length=0, max_length=0, avg_length=0.0)

        lengths = non_nulls.str.len()
        unique_cnt = non_nulls.nunique()
        is_unique_id = (unique_cnt == len(non_nulls)) and len(non_nulls) > 10

        return TextStats(
            min_length=int(lengths.min()),
            max_length=int(lengths.max()),
            avg_length=round(float(lengths.mean()), 1),
            is_unique_id=is_unique_id
        )

    def compute_data_quality_report(self, df: pd.DataFrame) -> DataQualityReport:
        """
        Calculates missing cells, duplicate rows, and health score (0-100).
        """
        total_rows = len(df)
        total_cols = len(df.columns)
        total_cells = total_rows * total_cols
        missing_cells = int(df.isna().sum().sum())
        missing_pct = round((missing_cells / total_cells * 100) if total_cells > 0 else 0.0, 2)

        duplicate_rows = int(df.duplicated().sum())
        dup_pct = round((duplicate_rows / total_rows * 100) if total_rows > 0 else 0.0, 2)

        complete_rows = int(df.dropna().shape[0])
        complete_rows_pct = round((complete_rows / total_rows * 100) if total_rows > 0 else 0.0, 2)

        penalties = (missing_pct * 0.4) + (dup_pct * 0.3)
        health_score = max(10.0, min(100.0, round(100.0 - penalties, 1)))

        warnings: List[QualityWarning] = []

        if missing_pct > 15.0:
            warnings.append(QualityWarning(
                warning_type="high_missing",
                message=f"Dataset has {missing_pct}% missing values across cells.",
                severity="warning" if missing_pct < 30 else "critical"
            ))

        if dup_pct > 5.0:
            warnings.append(QualityWarning(
                warning_type="duplicate_rows",
                message=f"Detected {duplicate_rows} duplicate rows ({dup_pct}%).",
                severity="warning"
            ))

        for col in df.columns:
            s = df[col]
            nulls = int(s.isna().sum())
            col_null_pct = (nulls / total_rows) * 100 if total_rows > 0 else 0
            if col_null_pct > 40.0:
                warnings.append(QualityWarning(
                    column=str(col),
                    warning_type="high_missing",
                    message=f"Column '{col}' has {col_null_pct:.1f}% missing values.",
                    severity="warning"
                ))
            if s.nunique() == 1 and total_rows > 1:
                warnings.append(QualityWarning(
                    column=str(col),
                    warning_type="constant_value",
                    message=f"Column '{col}' is constant (only 1 distinct value).",
                    severity="info"
                ))

        return DataQualityReport(
            health_score=health_score,
            total_cells=total_cells,
            missing_cells=missing_cells,
            missing_percentage=missing_pct,
            complete_rows_count=complete_rows,
            complete_rows_percentage=complete_rows_pct,
            duplicate_rows_count=duplicate_rows,
            duplicate_rows_percentage=dup_pct,
            memory_usage_bytes=int(df.memory_usage(deep=True).sum()),
            warnings=warnings
        )

    def identify_potential_metrics(
        self,
        df: pd.DataFrame,
        numeric_cols: List[str],
        identifier_cols: List[str]
    ) -> List[PotentialMetric]:
        """
        Identifies potential business metrics/KPIs dynamically without fixed column names.
        """
        potential_metrics: List[PotentialMetric] = []

        for col in numeric_cols:
            if col in identifier_cols:
                continue

            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(s) < 2 or s.nunique() <= 1:
                continue

            clean_key = str(col).lower().replace(" ", "_").replace("-", "_")
            mean_val = float(s.mean())
            std_val = float(s.std(ddof=1)) if len(s) > 1 else 0.0

            if s.min() >= 0 and s.max() <= 1.0:
                reason = "Ratio / Percentage metric (values bounded between 0 and 1)"
            elif s.min() >= 0 and s.sum() > s.mean():
                reason = f"Aggregatable business volume metric (Sum: {s.sum():,.2f}, Mean: {mean_val:,.2f})"
            else:
                reason = f"Continuous quantitative indicator (Mean: {mean_val:,.2f}, StdDev: {std_val:,.2f})"

            potential_metrics.append(PotentialMetric(
                name=str(col),
                key=clean_key,
                data_type="numeric",
                sum=round(float(s.sum()), 2),
                mean=round(mean_val, 2),
                median=round(float(s.median()), 2),
                min=round(float(s.min()), 2),
                max=round(float(s.max()), 2),
                std_dev=round(std_val, 2),
                reason=reason
            ))

        return potential_metrics

    def compute_correlations(self, df: pd.DataFrame) -> Tuple[Dict[str, Dict[str, float]], List[CorrelationPair]]:
        """
        Computes Pearson and Spearman correlation matrices for numeric features.
        """
        numeric_df = df.select_dtypes(include=[np.number]).dropna()
        if numeric_df.shape[1] < 2 or len(numeric_df) < 5:
            return {}, []

        corr_matrix_df = numeric_df.corr(method="pearson").round(3)
        corr_matrix = corr_matrix_df.to_dict()

        spearman_matrix_df = numeric_df.corr(method="spearman").round(3)

        strong_pairs: List[CorrelationPair] = []
        cols = list(numeric_df.columns)

        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                col_a = cols[i]
                col_b = cols[j]
                r_val = float(corr_matrix_df.loc[col_a, col_b])
                s_val = float(spearman_matrix_df.loc[col_a, col_b])
                abs_r = abs(r_val)

                if abs_r >= 0.40:
                    strength = "very_strong" if abs_r >= 0.80 else ("strong" if abs_r >= 0.65 else "moderate")
                    direction = "positive" if r_val > 0 else "negative"

                    strong_pairs.append(CorrelationPair(
                        column_x=str(col_a),
                        column_y=str(col_b),
                        pearson_r=r_val,
                        spearman_r=s_val,
                        strength=strength,
                        direction=direction
                    ))

        strong_pairs.sort(key=lambda p: abs(p.pearson_r), reverse=True)
        return corr_matrix, strong_pairs

    def generate_comprehensive_profile(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        project_id: str,
        name: str,
        file_type: str = "csv"
    ) -> DatasetProfile:
        """
        Generates full deterministic analytical DatasetProfile using Pandas/NumPy.
        """
        start_time = time.time()
        total_rows = len(df)
        total_cols = len(df.columns)

        # 1. Missing Values & Duplicate Summary
        quality_report = self.compute_data_quality_report(df)
        
        cols_with_missing = [str(c) for c in df.columns if df[c].isna().sum() > 0]
        missing_summary = MissingValuesSummary(
            total_cells=quality_report.total_cells,
            missing_cells=quality_report.missing_cells,
            missing_percentage=quality_report.missing_percentage,
            columns_with_missing=cols_with_missing
        )

        dup_summary = DuplicateSummary(
            duplicate_rows=quality_report.duplicate_rows_count,
            duplicate_percentage=quality_report.duplicate_rows_percentage
        )

        # 2. Type Detection & Classification Lists
        numeric_cols: List[str] = []
        categorical_cols: List[str] = []
        datetime_cols: List[str] = []
        identifier_cols: List[str] = []
        descriptive_stats_map: Dict[str, NumericStats] = {}

        detailed_columns: List[ColumnDetailedProfile] = []

        for col in df.columns:
            s = df[col]
            dtype, confidence = self.infer_column_type(s, str(col), total_rows)
            is_id = (dtype == "id")

            null_count = int(s.isna().sum())
            null_pct = round((null_count / total_rows * 100) if total_rows > 0 else 0.0, 2)
            unique_cnt = int(s.nunique())
            distinct_ratio = round((unique_cnt / total_rows) if total_rows > 0 else 0.0, 4)

            # Categorize into lists
            if is_id:
                identifier_cols.append(str(col))
            elif dtype == "numeric":
                numeric_cols.append(str(col))
            elif dtype in ["categorical", "boolean"]:
                categorical_cols.append(str(col))
            elif dtype == "datetime":
                datetime_cols.append(str(col))

            col_warnings = []
            if null_pct > 30.0:
                col_warnings.append(f"High missing rate ({null_pct}%)")
            if unique_cnt == 1:
                col_warnings.append("Constant column")

            numeric_stats = self.compute_numeric_stats(s) if dtype == "numeric" else None
            categorical_stats = self.compute_categorical_stats(s) if dtype in ["categorical", "boolean"] else None
            datetime_stats = self.compute_datetime_stats(s) if dtype == "datetime" else None
            text_stats = self.compute_text_stats(s) if dtype in ["text", "id"] else None

            if numeric_stats:
                descriptive_stats_map[str(col)] = numeric_stats

            clean_key = str(col).lower().replace(" ", "_").replace("-", "_")
            is_potential_metric = (dtype == "numeric" and not is_id and unique_cnt > 1)

            detailed_columns.append(ColumnDetailedProfile(
                name=str(col),
                key=clean_key,
                original_name=str(col),
                data_type=dtype,
                inferred_confidence=confidence,
                null_count=null_count,
                null_percentage=null_pct,
                unique_count=unique_cnt,
                total_count=total_rows,
                cardinality=unique_cnt,
                distinct_ratio=distinct_ratio,
                is_identifier=is_id,
                is_potential_metric=is_potential_metric,
                numeric_stats=numeric_stats,
                categorical_stats=categorical_stats,
                datetime_stats=datetime_stats,
                text_stats=text_stats,
                warnings=col_warnings
            ))

        # 3. Identify Potential Metrics
        potential_metrics = self.identify_potential_metrics(df, numeric_cols, identifier_cols)

        # 4. Multi-Variable Correlation Matrix
        corr_matrix, strong_correlations = self.compute_correlations(df)

        duration_ms = round((time.time() - start_time) * 1000, 2)

        return DatasetProfile(
            dataset_id=dataset_id,
            project_id=project_id,
            name=name,
            file_type=file_type,
            row_count=total_rows,
            column_count=total_cols,
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            datetime_columns=datetime_cols,
            identifier_columns=identifier_cols,
            potential_metrics=potential_metrics,
            missing_values_summary=missing_summary,
            duplicate_summary=dup_summary,
            quality_report=quality_report,
            columns=detailed_columns,
            descriptive_stats=descriptive_stats_map,
            strong_correlations=strong_correlations,
            correlation_matrix=corr_matrix,
            execution_time_ms=duration_ms
        )

    def profile_dataframe(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        project_id: str,
        name: str,
        original_filename: str,
        file_type: FileType,
        storage_bucket: str = "datasets",
        storage_path: Optional[str] = None,
        status: DatasetStatus = "completed",
        error_message: Optional[str] = None,
        processing_time_ms: Optional[float] = None
    ) -> Dataset:
        """
        Lightweight standard Dataset schema generator for dataset ingestion.
        """
        columns: List[DatasetColumn] = []
        for col_name in df.columns:
            series = df[col_name]
            dtype, _ = self.infer_column_type(series, str(col_name), len(df))
            clean_key = str(col_name).lower().replace(" ", "_").replace("-", "_")

            non_nulls = series.dropna()
            null_count = len(series) - len(non_nulls)
            unique_count = int(series.nunique())

            summary = DatasetColumnSummary(
                uniqueCount=unique_count,
                nullCount=null_count,
                totalCount=len(series)
            )

            if dtype == "numeric" and len(non_nulls) > 0:
                num_s = pd.to_numeric(non_nulls, errors="coerce").dropna()
                if len(num_s) > 0:
                    summary.min = float(num_s.min())
                    summary.max = float(num_s.max())
                    summary.mean = round(float(num_s.mean()), 2)
                    summary.median = round(float(num_s.median()), 2)
                    summary.stdDev = round(float(num_s.std()), 2) if len(num_s) > 1 else 0.0

                    if summary.max > summary.min:
                        bins = np.linspace(summary.min, summary.max, 6)
                        counts, _ = np.histogram(num_s, bins=bins)
                        distribution = []
                        for i in range(len(counts)):
                            b_label = f"{bins[i]:.1f} - {bins[i+1]:.1f}"
                            distribution.append(SimpleHistogramBucket(bucket=b_label, count=int(counts[i])))
                        summary.distribution = distribution

            elif dtype in ["categorical", "boolean"] and len(non_nulls) > 0:
                top_counts = non_nulls.value_counts().head(8)
                top_cats = []
                for label, cnt in top_counts.items():
                    pct = round((cnt / len(non_nulls)) * 100, 1)
                    top_cats.append(CategoryCount(label=str(label), count=int(cnt), percentage=pct))
                summary.topCategories = top_cats

            columns.append(DatasetColumn(
                name=str(col_name),
                key=clean_key,
                originalName=str(col_name),
                dataType=dtype,
                summary=summary,
                description=f"Inferred {dtype} metric with {summary.uniqueCount} distinct values"
            ))

        clean_sample_df = df.head(100).replace({np.nan: None})
        sample_rows_raw = clean_sample_df.to_dict(orient="records")
        sample_rows = []

        for row in sample_rows_raw:
            enhanced_row = {}
            for col_obj in columns:
                raw_val = row.get(col_obj.originalName)
                if raw_val is None:
                    raw_val = row.get(col_obj.name)
                if raw_val is None:
                    raw_val = row.get(col_obj.key)

                if isinstance(raw_val, (pd.Timestamp, np.datetime64)):
                    raw_val = str(raw_val)
                elif isinstance(raw_val, (np.integer, np.int64)):
                    raw_val = int(raw_val)
                elif isinstance(raw_val, (np.floating, np.float64)):
                    raw_val = None if np.isnan(raw_val) else float(raw_val)

                enhanced_row[col_obj.key] = raw_val
                enhanced_row[col_obj.name] = raw_val
                enhanced_row[col_obj.originalName] = raw_val
            sample_rows.append(enhanced_row)

        return Dataset(
            id=dataset_id,
            projectId=project_id,
            name=name,
            description=f"Uploaded {file_type.upper()} dataset with {len(df)} rows and {len(df.columns)} columns",
            rowCount=len(df),
            columnCount=len(df.columns),
            columns=columns,
            sampleRows=sample_rows,
            sizeBytes=int(df.memory_usage(deep=True).sum()),
            fileType=file_type,
            fileName=original_filename,
            storageBucket=storage_bucket,
            storagePath=storage_path,
            status=status,
            errorMessage=error_message,
            processingTimeMs=processing_time_ms,
            tags=[file_type.upper(), f"{len(df)} rows"]
        )

profiler = DynamicDatasetProfiler()
