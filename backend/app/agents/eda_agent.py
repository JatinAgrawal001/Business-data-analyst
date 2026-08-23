import uuid
import time
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from google.adk.agents import Agent
from app.schemas.profiler import DatasetProfile, NumericStats, HistogramBucket
from app.schemas.eda import (
    EDAReport,
    EDASummary,
    KPIEntry,
    SegmentAnalysis,
    SegmentBreakdownEntry,
    CategoryAnalysisEntry,
    ColumnOutlierReport,
    TimeSeriesTrend,
    TimeSeriesPoint,
    CorrelationInsight,
    CorrelationSummary,
    ChartRecommendation,
    EDAInsight,
    ChartType
)
from app.core.logging import get_logger

logger = get_logger("app.agents.eda")

class EDAAgent:
    """
    Google ADK-powered Dynamic Exploratory Data Analysis (EDA) Agent.
    Strictly Python/Pandas-calculated deterministic analytics for arbitrary datasets:
    - descriptive statistics
    - distributions
    - correlations
    - category analysis
    - time trends
    - group-by analysis
    - outlier analysis
    - relevant KPIs
    Zero reliance on hardcoded column names (e.g. sales, revenue, profit, customers).
    """

    def __init__(self):
        self._setup_adk_agent()

    def _setup_adk_agent(self):
        try:
            self.adk_agent = Agent(
                name="eda_agent",
                model="gemini-2.5-flash",
                instruction=(
                    "You are an expert Exploratory Data Analysis (EDA) Agent. "
                    "Analyze arbitrary tabular dataset profiles and distributions to uncover hidden business patterns, "
                    "segment behaviors, temporal seasonality, strong feature correlations, and recommended visualization blueprints. "
                    "Do not assume fixed column names."
                ),
                description="Performs automated exploratory data analysis and visual chart generation."
            )
        except Exception as e:
            logger.warning(f"ADK EDA Agent init notice: {e}")
            self.adk_agent = None

    def compute_relevant_kpis(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile
    ) -> List[KPIEntry]:
        """
        Dynamically extracts top business KPIs from non-identifier numerical columns.
        Uses pure Pandas deterministic calculations.
        """
        kpis: List[KPIEntry] = []
        
        for col_profile in profile.columns:
            if col_profile.data_type == "numeric" and col_profile.numeric_stats:
                col_name = col_profile.name
                stats = col_profile.numeric_stats
                
                val = stats.sum if stats.sum != 0 else stats.mean
                agg_type = "sum" if stats.sum != 0 else "mean"
                metric_type = "volume" if stats.sum > 1000 else "average"
                
                if abs(val) >= 1_000_000:
                    formatted_val = f"{val / 1_000_000:.2f}M"
                elif abs(val) >= 1_000:
                    formatted_val = f"{val / 1_000:.2f}K"
                else:
                    formatted_val = f"{val:.2f}"

                human_title = col_name.replace("_", " ").title()

                kpis.append(KPIEntry(
                    title=f"Total {human_title}" if agg_type == "sum" else f"Avg {human_title}",
                    key=col_name,
                    value=round(val, 2),
                    formatted_value=formatted_val,
                    aggregation_type=agg_type,
                    metric_type=metric_type,
                    description=f"Aggregate {agg_type} for feature '{col_name}' (Mean: {stats.mean:.2f}, Median: {stats.median:.2f})"
                ))

        return kpis[:6]

    def compute_category_analysis(
        self,
        profile: DatasetProfile
    ) -> List[CategoryAnalysisEntry]:
        """
        Extracts deterministic categorical distributions, cardinality, mode, and Shannon entropy.
        """
        entries: List[CategoryAnalysisEntry] = []
        for col_profile in profile.columns:
            if col_profile.data_type in ["categorical", "text"] and col_profile.categorical_stats:
                cat = col_profile.categorical_stats
                entries.append(CategoryAnalysisEntry(
                    column=col_profile.name,
                    cardinality=cat.cardinality,
                    distinct_ratio=cat.distinct_ratio,
                    mode=cat.mode,
                    entropy=cat.entropy,
                    top_categories=cat.top_categories
                ))
        return entries

    def compute_outlier_reports(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile
    ) -> List[ColumnOutlierReport]:
        """
        Computes deterministic Tukey's IQR outlier analysis for every numeric feature.
        """
        outlier_reports: List[ColumnOutlierReport] = []
        for col_profile in profile.columns:
            if col_profile.data_type == "numeric" and col_profile.numeric_stats:
                stats = col_profile.numeric_stats
                out = stats.outliers
                if out:
                    sample_vals: List[float] = []
                    if col_profile.name in df.columns:
                        s = df[col_profile.name].dropna()
                        out_mask = (s < out.iqr_lower_bound) | (s > out.iqr_upper_bound)
                        sample_vals = [round(float(v), 2) for v in s[out_mask].head(5).tolist()]

                    severity = "severe" if out.outlier_percentage > 5.0 else ("moderate" if out.outlier_percentage > 0 else "none")

                    outlier_reports.append(ColumnOutlierReport(
                        column=col_profile.name,
                        outlier_count=out.outlier_count,
                        outlier_percentage=out.outlier_percentage,
                        iqr_lower_bound=out.iqr_lower_bound,
                        iqr_upper_bound=out.iqr_upper_bound,
                        sample_outliers=sample_vals,
                        severity=severity
                    ))
        return outlier_reports

    def compute_group_by_analysis(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile
    ) -> List[SegmentAnalysis]:
        """
        Computes dynamic group-by multidimensional aggregations.
        Picks primary numeric metrics and groups by top categorical dimensions.
        """
        segments: List[SegmentAnalysis] = []
        numeric_cols = [c.name for c in profile.columns if c.data_type == "numeric"]
        cat_cols = [c.name for c in profile.columns if c.data_type == "categorical"]

        if not numeric_cols or not cat_cols:
            return segments

        primary_metric = numeric_cols[0]

        for cat_col in cat_cols[:4]:
            if cat_col not in df.columns or primary_metric not in df.columns:
                continue

            clean_df = df[[cat_col, primary_metric]].dropna()
            if len(clean_df) == 0:
                continue

            grouped = clean_df.groupby(cat_col)[primary_metric].agg(
                metric_sum="sum",
                metric_mean="mean",
                record_count="count"
            ).reset_index()

            grouped = grouped.sort_values(by="metric_sum", ascending=False).head(8)
            total_sum = grouped["metric_sum"].sum()

            breakdown_entries: List[SegmentBreakdownEntry] = []
            for _, row in grouped.iterrows():
                m_sum = float(row["metric_sum"])
                m_mean = float(row["metric_mean"])
                cnt = int(row["record_count"])
                pct = round((m_sum / total_sum * 100), 1) if total_sum > 0 else 0.0

                breakdown_entries.append(SegmentBreakdownEntry(
                    category=str(row[cat_col]),
                    metric_sum=round(m_sum, 2),
                    metric_mean=round(m_mean, 2),
                    record_count=cnt,
                    percentage=pct
                ))

            if breakdown_entries:
                top_seg = breakdown_entries[0]
                insight_str = f"'{top_seg.category}' is the primary segment in '{cat_col}', accounting for {top_seg.percentage}% of aggregate '{primary_metric}'."
                segments.append(SegmentAnalysis(
                    dimension_column=cat_col,
                    metric_column=primary_metric,
                    top_segments=breakdown_entries,
                    insight=insight_str
                ))

        return segments

    def compute_time_trends(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile
    ) -> Optional[TimeSeriesTrend]:
        """
        Dynamically analyzes chronological progression and growth rate if a datetime column exists.
        """
        datetime_cols = profile.datetime_columns
        numeric_cols = [c.name for c in profile.columns if c.data_type == "numeric"]

        if not datetime_cols or not numeric_cols:
            return None

        date_col = datetime_cols[0]
        metric_col = numeric_cols[0]

        if date_col not in df.columns or metric_col not in df.columns:
            return None

        clean_df = df[[date_col, metric_col]].dropna().copy()
        clean_df["parsed_date"] = pd.to_datetime(clean_df[date_col], errors="coerce")
        clean_df = clean_df.dropna(subset=["parsed_date"])

        if len(clean_df) < 2:
            return None

        clean_df["date_str"] = clean_df["parsed_date"].dt.strftime("%Y-%m-%d")
        grouped = clean_df.groupby("date_str")[metric_col].agg(value="sum", record_count="count").reset_index()
        grouped = grouped.sort_values(by="date_str")

        data_points = [
            TimeSeriesPoint(period=str(r["date_str"]), value=round(float(r["value"]), 2), record_count=int(r["record_count"]))
            for _, r in grouped.iterrows()
        ]

        if len(data_points) < 2:
            return None

        first_val = data_points[0].value
        last_val = data_points[-1].value
        growth_rate = round(((last_val - first_val) / first_val * 100), 2) if first_val != 0 else 0.0

        trend_direction = "upward" if growth_rate > 5.0 else ("downward" if growth_rate < -5.0 else "stable")
        insight_str = f"Over the observed timespan, '{metric_col}' shows an overall {trend_direction} trajectory with {growth_rate:+0.1f}% net change."

        return TimeSeriesTrend(
            time_column=date_col,
            metric_column=metric_col,
            granularity="daily",
            trend_direction=trend_direction,
            growth_rate=growth_rate,
            data_points=data_points,
            insight=insight_str
        )

    def generate_chart_recommendations(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile,
        segments: List[SegmentAnalysis],
        time_series: Optional[TimeSeriesTrend]
    ) -> List[ChartRecommendation]:
        """
        Generates dynamic UI chart configurations without hardcoded column names.
        """
        charts: List[ChartRecommendation] = []

        # 1. Bar Chart
        if segments:
            seg = segments[0]
            charts.append(ChartRecommendation(
                id="chart-bar-01",
                title=f"{seg.metric_column.replace('_', ' ').title()} by {seg.dimension_column.replace('_', ' ').title()}",
                chart_type="bar",
                x_axis="category",
                y_axis="value",
                group_by=seg.dimension_column,
                description=f"Comparative performance breakdown across {seg.dimension_column} categories.",
                data=[{"category": s.category, "value": s.metric_sum, "count": s.record_count} for s in seg.top_segments]
            ))

        # 2. Donut Chart
        if segments:
            seg = segments[0]
            charts.append(ChartRecommendation(
                id="chart-donut-01",
                title=f"Distribution Share ({seg.dimension_column.replace('_', ' ').title()})",
                chart_type="donut",
                x_axis="name",
                y_axis="value",
                description=f"Proportional breakdown of {seg.metric_column} across categories.",
                data=[{"name": s.category, "value": s.percentage} for s in seg.top_segments]
            ))

        # 3. Line Chart
        if time_series and len(time_series.data_points) >= 2:
            charts.append(ChartRecommendation(
                id="chart-line-01",
                title=f"Chronological Trend: {time_series.metric_column.replace('_', ' ').title()}",
                chart_type="line",
                x_axis="period",
                y_axis="value",
                description=f"Time-series trajectory with {time_series.growth_rate:+0.1f}% net change.",
                data=[{"period": pt.period, "value": pt.value} for pt in time_series.data_points]
            ))

        # 4. Scatter Plot
        if profile.strong_correlations:
            top_corr = profile.strong_correlations[0]
            col_x = top_corr.column_x
            col_y = top_corr.column_y
            if col_x in df.columns and col_y in df.columns:
                scatter_df = df[[col_x, col_y]].dropna().head(50)
                charts.append(ChartRecommendation(
                    id="chart-scatter-01",
                    title=f"Correlation: {col_x.replace('_', ' ').title()} vs {col_y.replace('_', ' ').title()} (r={top_corr.pearson_r:.2f})",
                    chart_type="scatter",
                    x_axis="x",
                    y_axis="y",
                    description=f"Scatter distribution demonstrating {top_corr.strength} correlation.",
                    data=[{"x": float(r[col_x]), "y": float(r[col_y])} for _, r in scatter_df.iterrows()]
                ))

        return charts

    def generate_eda_report(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile
    ) -> EDAReport:
        """
        Executes full automated dynamic EDA and synthesizes structured analytical deliverables.
        Pure Python / Pandas calculations. Works for any arbitrary dataset.
        """
        start_time = time.time()
        total_rows = len(df)
        total_cols = len(df.columns)

        # 1. Descriptive Statistics & Distributions
        desc_stats: Dict[str, NumericStats] = {}
        distributions: Dict[str, List[HistogramBucket]] = {}
        for col_profile in profile.columns:
            if col_profile.data_type == "numeric" and col_profile.numeric_stats:
                desc_stats[col_profile.name] = col_profile.numeric_stats
                distributions[col_profile.name] = col_profile.numeric_stats.distribution

        # 2. Dynamic Modules
        kpis = self.compute_relevant_kpis(df, profile)
        cat_analysis = self.compute_category_analysis(profile)
        outlier_reports = self.compute_outlier_reports(df, profile)
        segments = self.compute_group_by_analysis(df, profile)
        time_trends = self.compute_time_trends(df, profile)
        chart_recs = self.generate_chart_recommendations(df, profile, segments, time_trends)

        # 3. Correlations Summary
        corr_insights: List[CorrelationInsight] = []
        for corr in profile.strong_correlations:
            interp = f"Significant {corr.direction} association (r={corr.pearson_r:0.2f}) between {corr.column_x} and {corr.column_y}."
            corr_insights.append(CorrelationInsight(
                feature_x=corr.column_x,
                feature_y=corr.column_y,
                pearson_r=corr.pearson_r,
                spearman_r=corr.spearman_r,
                strength=corr.strength if corr.strength != "very_strong" else "strong",
                direction=corr.direction,
                interpretation=interp
            ))

        corr_matrix = profile.correlation_matrix or {}
        corr_summary = CorrelationSummary(
            matrix=corr_matrix,
            ranked_pairs=corr_insights
        )

        # 4. Insights Generation
        insights: List[EDAInsight] = []
        if segments:
            top_seg = segments[0].top_segments[0]
            insights.append(EDAInsight(
                id=str(uuid.uuid4()),
                title=f"Category Concentration in {top_seg.category}",
                category="segment",
                priority="high",
                description=f"The '{top_seg.category}' segment contributes {top_seg.percentage}% of aggregate volume.",
                action_suggested="Target marketing and resource allocation towards high-yield segments."
            ))

        if time_trends:
            insights.append(EDAInsight(
                id=str(uuid.uuid4()),
                title=f"Temporal Direction: {time_trends.trend_direction.title()}",
                category="trend",
                priority="high" if abs(time_trends.growth_rate) > 10 else "medium",
                description=f"Observed net growth rate of {time_trends.growth_rate:+0.1f}% over the tracked timeline.",
                action_suggested="Implement trend-following forecasting models."
            ))

        if corr_insights:
            top_c = corr_insights[0]
            insights.append(EDAInsight(
                id=str(uuid.uuid4()),
                title=f"Feature Dependency: {top_c.feature_x} & {top_c.feature_y}",
                category="correlation",
                priority="medium",
                description=top_c.interpretation,
                action_suggested="Account for collinearity during multivariate predictive modeling."
            ))

        # 5. Executive Summary
        primary_metric = kpis[0].key if kpis else (profile.numeric_columns[0] if profile.numeric_columns else None)
        primary_dim = segments[0].dimension_column if segments else (profile.categorical_columns[0] if profile.categorical_columns else None)

        takeaways = [
            f"Dataset contains {total_rows:,} records across {total_cols} dimensions with {profile.quality_report.health_score:.1f}/100 data hygiene rating.",
            f"Identified {len(profile.numeric_columns)} numeric metrics, {len(profile.categorical_columns)} categorical groupings, and {len(profile.datetime_columns)} temporal sequences.",
            f"Extracted {len(kpis)} relevant KPIs, {len(segments)} group-by segmentations, and {len(chart_recs)} recommended visualization blueprints."
        ]

        overview_text = (
            f"Automated dynamic Exploratory Data Analysis conducted on '{profile.name}'. "
            f"Total observations: {total_rows}, Total attributes: {total_cols}. "
            f"Primary quantitative driver: '{primary_metric or 'N/A'}' across dimension '{primary_dim or 'N/A'}'."
        )

        summary = EDASummary(
            overview=overview_text,
            total_rows=total_rows,
            total_columns=total_cols,
            numeric_columns_count=len(profile.numeric_columns),
            categorical_columns_count=len(profile.categorical_columns),
            datetime_columns_count=len(profile.datetime_columns),
            primary_metric=primary_metric,
            primary_dimension=primary_dim,
            key_takeaways=takeaways
        )

        duration_ms = round((time.time() - start_time) * 1000, 2)

        return EDAReport(
            dataset_id=profile.dataset_id,
            dataset_name=profile.name,
            summary=summary,
            kpis=kpis,
            descriptive_statistics=desc_stats,
            distributions=distributions,
            category_analysis=cat_analysis,
            time_trends=time_trends,
            group_by_analysis=segments,
            outlier_analysis=outlier_reports,
            correlations=corr_summary,
            chart_recommendations=chart_recs,
            insights=insights,
            execution_time_ms=duration_ms
        )

eda_agent = EDAAgent()
