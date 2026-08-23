import uuid
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from google.adk.agents import Agent
from app.schemas.profiler import DatasetProfile
from app.schemas.eda import EDAReport
from app.schemas.visualization import (
    VisualChartType,
    ColorTheme,
    AggregationFunction,
    VisualKPI,
    ChartSeriesConfig,
    VisualChartConfig,
    VisualChart,
    VisualizationDashboardResponse,
    CustomChartRequest,
    CustomChartResponse
)
from app.core.logging import get_logger

logger = get_logger("app.agents.visualization")

THEME_PALETTES: Dict[ColorTheme, List[str]] = {
    "indigo_modern": ["#6366f1", "#8b5cf6", "#ec4899", "#3b82f6", "#14b8a6", "#f59e0b", "#10b981"],
    "emerald_growth": ["#10b981", "#059669", "#34d399", "#6ee7b7", "#047857", "#14b8a6", "#3b82f6"],
    "sunset_amber": ["#f97316", "#ef4444", "#f59e0b", "#ec4899", "#8b5cf6", "#6366f1", "#10b981"],
    "cyber_neon": ["#06b6d4", "#3b82f6", "#8b5cf6", "#ec4899", "#10b981", "#f59e0b", "#a855f7"],
    "slate_executive": ["#334155", "#475569", "#64748b", "#94a3b8", "#cbd5e1", "#0ea5e9", "#6366f1"]
}

class VisualizationAgent:
    """
    Google ADK-powered Visualization Agent.
    Dynamically selects suitable charts based on DatasetProfile, EDA results, and KPIs:
    - line (time trends)
    - bar (categorical comparisons with high-cardinality guardrails)
    - scatter (multivariate correlations)
    - histogram (distribution frequencies)
    - box_plot (five-number statistical box plot)
    - heatmap (correlation matrix grid)
    - kpi_card (executive summary cards)
    
    Zero fake values. Strict Python/Pandas calculation.
    """

    def __init__(self):
        self._setup_adk_agent()

    def _setup_adk_agent(self):
        try:
            self.adk_agent = Agent(
                name="visualization_agent",
                model="gemini-2.5-flash",
                instruction=(
                    "You are an expert Data Visualization Agent. "
                    "Dynamically select suitable visual chart types (line, bar, scatter, histogram, box plot, heatmap, KPI) "
                    "based on dataset profiles and EDA statistics. Avoid unreadable high-cardinality charts."
                ),
                description="Generates executive dashboard layouts and custom interactive charts."
            )
        except Exception as e:
            logger.warning(f"ADK Visualization Agent init notice: {e}")
            self.adk_agent = None

    def generate_kpis(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile,
        eda_report: Optional[EDAReport] = None
    ) -> List[VisualKPI]:
        """
        Extracts executive KPI cards from top numerical metrics or EDA results.
        """
        kpis: List[VisualKPI] = []

        if eda_report and eda_report.kpis:
            for k in eda_report.kpis[:4]:
                kpis.append(VisualKPI(
                    id=str(uuid.uuid4()),
                    title=k.title,
                    key=k.key,
                    value=k.value,
                    formatted_value=k.formatted_value,
                    aggregation=k.aggregation_type,
                    trend_indicator="positive" if k.value > 0 else "neutral",
                    subtext=k.description
                ))
            return kpis

        numeric_cols = [c.name for c in profile.columns if c.data_type == "numeric" and c.numeric_stats]
        for col_name in numeric_cols[:4]:
            if col_name not in df.columns:
                continue

            s = df[col_name].dropna()
            if len(s) == 0:
                continue

            total_val = float(s.sum())
            mean_val = float(s.mean())

            use_sum = total_val > 100
            display_val = total_val if use_sum else mean_val
            agg_type: AggregationFunction = "sum" if use_sum else "mean"

            if abs(display_val) >= 1_000_000:
                formatted = f"{display_val / 1_000_000:.2f}M"
            elif abs(display_val) >= 1_000:
                formatted = f"{display_val / 1_000:.2f}K"
            else:
                formatted = f"{display_val:.2f}"

            human_title = col_name.replace("_", " ").title()

            kpis.append(VisualKPI(
                id=str(uuid.uuid4()),
                title=f"Total {human_title}" if use_sum else f"Avg {human_title}",
                key=col_name,
                value=round(display_val, 2),
                formatted_value=formatted,
                aggregation=agg_type,
                trend_indicator="positive" if display_val > 0 else "neutral",
                subtext=f"{agg_type.title()} across {len(s):,} records (Mean: {mean_val:.2f})"
            ))

        return kpis

    def generate_dashboard(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile,
        eda_report: Optional[EDAReport] = None,
        theme: ColorTheme = "indigo_modern"
    ) -> VisualizationDashboardResponse:
        """
        Generates a curated multi-chart interactive dashboard with all supported chart types:
        - bar (with high-cardinality protection)
        - line (time trend)
        - scatter (correlation)
        - histogram (distribution)
        - box_plot (five-number summary)
        - heatmap (correlation matrix)
        - kpi_card (executive summary metrics)
        """
        palette = THEME_PALETTES.get(theme, THEME_PALETTES["indigo_modern"])
        charts: List[VisualChart] = []
        kpis = self.generate_kpis(df, profile, eda_report)

        numeric_cols = [c.name for c in profile.columns if c.data_type == "numeric"]
        # Filter categorical columns to avoid high-cardinality unreadable dimensions (unique <= 25)
        cat_cols = [
            c.name for c in profile.columns
            if c.data_type == "categorical" and c.categorical_stats and c.categorical_stats.cardinality <= 25
        ]
        date_cols = profile.datetime_columns

        primary_metric = numeric_cols[0] if numeric_cols else None
        secondary_metric = numeric_cols[1] if len(numeric_cols) > 1 else None
        primary_dim = cat_cols[0] if cat_cols else None

        # =========================================================================
        # 1. Bar Chart: Categorical Comparison with High-Cardinality Guardrails
        # =========================================================================
        if primary_dim and primary_metric and primary_dim in df.columns and primary_metric in df.columns:
            clean_df = df[[primary_dim, primary_metric]].dropna()
            grouped = clean_df.groupby(primary_dim)[primary_metric].sum().reset_index()
            grouped = grouped.sort_values(by=primary_metric, ascending=False)
            
            # High-cardinality guard: Cap at Top 10 + "Others"
            if len(grouped) > 10:
                top_10 = grouped.head(10)
                other_sum = float(grouped.iloc[10:][primary_metric].sum())
                other_row = pd.DataFrame([{primary_dim: "Other", primary_metric: other_sum}])
                grouped = pd.concat([top_10, other_row], ignore_index=True)

            bar_data = [
                {"category": str(r[primary_dim]), "value": round(float(r[primary_metric]), 2)}
                for _, r in grouped.iterrows()
            ]

            if bar_data:
                charts.append(VisualChart(
                    id="dash-chart-bar",
                    config=VisualChartConfig(
                        chart_type="bar",
                        title=f"{primary_metric.replace('_', ' ').title()} by {primary_dim.replace('_', ' ').title()}",
                        subtitle=f"Aggregated volume across top {primary_dim} categories",
                        x_axis_key="category",
                        x_axis_label=primary_dim.replace('_', ' ').title(),
                        y_axis_key="value",
                        y_axis_label=primary_metric.replace('_', ' ').title(),
                        series=[ChartSeriesConfig(name=primary_metric.replace('_', ' ').title(), data_key="value", color=palette[0])],
                        color_palette=palette,
                        card_width="half"
                    ),
                    data=bar_data,
                    storytelling_caption=f"'{bar_data[0]['category']}' leads category volume with {bar_data[0]['value']:,.2f} total {primary_metric}."
                ))

        # =========================================================================
        # 2. Line Chart: Time-Series Trend
        # =========================================================================
        if date_cols and primary_metric and date_cols[0] in df.columns and primary_metric in df.columns:
            date_col = date_cols[0]
            clean_df = df[[date_col, primary_metric]].dropna().copy()
            clean_df["parsed_date"] = pd.to_datetime(clean_df[date_col], errors="coerce")
            clean_df = clean_df.dropna(subset=["parsed_date"])

            if len(clean_df) >= 2:
                clean_df["period"] = clean_df["parsed_date"].dt.strftime("%Y-%m-%d")
                grouped = clean_df.groupby("period")[primary_metric].sum().reset_index().sort_values(by="period")

                line_data = [
                    {"period": str(r["period"]), "value": round(float(r[primary_metric]), 2)}
                    for _, r in grouped.iterrows()
                ]

                first_val = line_data[0]["value"]
                last_val = line_data[-1]["value"]
                growth = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0.0

                charts.append(VisualChart(
                    id="dash-chart-line",
                    config=VisualChartConfig(
                        chart_type="line",
                        title=f"{primary_metric.replace('_', ' ').title()} Over Time",
                        subtitle=f"Chronological trend tracking across {len(line_data)} observations",
                        x_axis_key="period",
                        x_axis_label="Date",
                        y_axis_key="value",
                        y_axis_label=primary_metric.replace('_', ' ').title(),
                        series=[ChartSeriesConfig(name=primary_metric.replace('_', ' ').title(), data_key="value", color=palette[1])],
                        color_palette=palette,
                        card_width="half"
                    ),
                    data=line_data,
                    storytelling_caption=f"Time trend displays a {growth:+0.1f}% net progression over the observed timeline."
                ))

        # =========================================================================
        # 3. Scatter Plot: Multi-Variable Correlation
        # =========================================================================
        if profile.strong_correlations:
            top_corr = profile.strong_correlations[0]
            cx, cy = top_corr.column_x, top_corr.column_y
            if cx in df.columns and cy in df.columns:
                scatter_df = df[[cx, cy]].dropna().head(60)
                scatter_data = [
                    {"x": round(float(r[cx]), 2), "y": round(float(r[cy]), 2)}
                    for _, r in scatter_df.iterrows()
                ]
                charts.append(VisualChart(
                    id="dash-chart-scatter",
                    config=VisualChartConfig(
                        chart_type="scatter",
                        title=f"Correlation: {cx.replace('_', ' ').title()} vs {cy.replace('_', ' ').title()}",
                        subtitle=f"Pearson r = {top_corr.pearson_r:.2f} ({top_corr.strength} {top_corr.direction})",
                        x_axis_key="x",
                        x_axis_label=cx.replace('_', ' ').title(),
                        y_axis_key="y",
                        y_axis_label=cy.replace('_', ' ').title(),
                        color_palette=palette,
                        card_width="half"
                    ),
                    data=scatter_data,
                    storytelling_caption=f"Strong relationship (r={top_corr.pearson_r:.2f}). Changes in {cx} align with {cy} variations."
                ))

        # =========================================================================
        # 4. Histogram: Value Distribution
        # =========================================================================
        if primary_metric:
            col_prof = next((c for c in profile.columns if c.name == primary_metric), None)
            if col_prof and col_prof.numeric_stats and col_prof.numeric_stats.distribution:
                hist_data = [
                    {"bin": b.bucket, "count": b.count, "percentage": b.percentage}
                    for b in col_prof.numeric_stats.distribution
                ]
                charts.append(VisualChart(
                    id="dash-chart-histogram",
                    config=VisualChartConfig(
                        chart_type="histogram",
                        title=f"{primary_metric.replace('_', ' ').title()} Frequency Distribution",
                        subtitle="5-bucket histogram frequency spread",
                        x_axis_key="bin",
                        x_axis_label="Bin Range",
                        y_axis_key="count",
                        y_axis_label="Frequency Count",
                        color_palette=palette,
                        card_width="half"
                    ),
                    data=hist_data,
                    storytelling_caption=f"Primary peak frequency concentrated in bin '{hist_data[0]['bin']}' with {hist_data[0]['count']} occurrences."
                ))

        # =========================================================================
        # 5. Box Plot: Five-Number Statistical Summary
        # =========================================================================
        if primary_metric and primary_metric in df.columns:
            s = df[primary_metric].dropna()
            if len(s) >= 4:
                q1 = float(s.quantile(0.25))
                med = float(s.median())
                q3 = float(s.quantile(0.75))
                iqr = q3 - q1
                lower_whisker = float(max(s.min(), q1 - 1.5 * iqr))
                upper_whisker = float(min(s.max(), q3 + 1.5 * iqr))
                outliers = [round(float(v), 2) for v in s[(s < lower_whisker) | (s > upper_whisker)].head(10).tolist()]

                box_data = [{
                    "column": primary_metric,
                    "min": round(lower_whisker, 2),
                    "q1": round(q1, 2),
                    "median": round(med, 2),
                    "q3": round(q3, 2),
                    "max": round(upper_whisker, 2),
                    "iqr": round(iqr, 2),
                    "outliers": outliers
                }]

                charts.append(VisualChart(
                    id="dash-chart-boxplot",
                    config=VisualChartConfig(
                        chart_type="box_plot",
                        title=f"{primary_metric.replace('_', ' ').title()} Box Plot Summary",
                        subtitle=f"Five-number summary (Median: {med:.2f}, IQR: {iqr:.2f})",
                        x_axis_key="column",
                        y_axis_key="median",
                        color_palette=palette,
                        card_width="half"
                    ),
                    data=box_data,
                    storytelling_caption=f"Median value is {med:.2f} with IQR span [{q1:.2f}, {q3:.2f}]. Detected {len(outliers)} outlier points."
                ))

        # =========================================================================
        # 6. Heatmap: Multi-Variable Correlation Matrix Grid
        # =========================================================================
        if profile.correlation_matrix and len(profile.correlation_matrix) >= 2:
            matrix = profile.correlation_matrix
            heatmap_data: List[Dict[str, Any]] = []
            cols_list = list(matrix.keys())[:6]  # Limit to top 6 continuous variables for clean UI
            for row_col in cols_list:
                for col_col in cols_list:
                    r_val = matrix.get(row_col, {}).get(col_col, 0.0)
                    heatmap_data.append({
                        "x": col_col,
                        "y": row_col,
                        "value": round(float(r_val), 2)
                    })

            charts.append(VisualChart(
                id="dash-chart-heatmap",
                config=VisualChartConfig(
                    chart_type="heatmap",
                    title="Correlation Matrix Heatmap",
                    subtitle="Pairwise Pearson correlation coefficients",
                    x_axis_key="x",
                    y_axis_key="y",
                    color_palette=palette,
                    card_width="full"
                ),
                data=heatmap_data,
                storytelling_caption=f"Pairwise matrix across {len(cols_list)} numeric dimensions displaying feature associations."
            ))

        return VisualizationDashboardResponse(
            dataset_id=profile.dataset_id,
            dataset_name=profile.name,
            total_charts=len(charts),
            theme=theme,
            kpi_cards=kpis,
            charts=charts
        )

    def generate_custom_chart(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile,
        request: CustomChartRequest,
        theme: ColorTheme = "indigo_modern"
    ) -> CustomChartResponse:
        """
        Dynamically generates a custom chart based on natural language query or explicit parameters.
        """
        palette = THEME_PALETTES.get(theme, THEME_PALETTES["indigo_modern"])
        query = (request.query or "").lower().strip()

        numeric_cols = [c.name for c in profile.columns if c.data_type == "numeric"]
        cat_cols = [c.name for c in profile.columns if c.data_type == "categorical" and c.categorical_stats and c.categorical_stats.cardinality <= 25]
        date_cols = profile.datetime_columns

        dim_col = request.dimension_column
        metric_col = request.metric_column
        chart_type = request.preferred_chart_type
        agg: AggregationFunction = request.aggregation or "sum"

        # Resolve dimension column if not specified
        if not dim_col:
            for c in cat_cols + date_cols:
                if c.lower() in query or c.lower().replace("_", " ") in query:
                    dim_col = c
                    break
            if not dim_col:
                dim_col = cat_cols[0] if cat_cols else (date_cols[0] if date_cols else df.columns[0])

        # Resolve metric column if not specified
        if not metric_col:
            for m in numeric_cols:
                if m.lower() in query or m.lower().replace("_", " ") in query:
                    metric_col = m
                    break
            if not metric_col:
                metric_col = numeric_cols[0] if numeric_cols else df.columns[1]

        # Resolve chart type if not specified
        if not chart_type:
            if "box" in query or "outlier" in query or "quantile" in query:
                chart_type = "box_plot"
            elif "histogram" in query or "distribution" in query:
                chart_type = "histogram"
            elif "heatmap" in query or "matrix" in query:
                chart_type = "heatmap"
            elif "scatter" in query or "correlation" in query:
                chart_type = "scatter"
            elif dim_col in date_cols or "time" in query or "trend" in query:
                chart_type = "line"
            else:
                chart_type = "bar"

        # Perform deterministic aggregation
        chart_data: List[Dict[str, Any]] = []
        caption = ""

        if chart_type == "box_plot" and metric_col in df.columns:
            s = df[metric_col].dropna()
            q1 = float(s.quantile(0.25))
            med = float(s.median())
            q3 = float(s.quantile(0.75))
            iqr = q3 - q1
            chart_data = [{
                "column": metric_col,
                "min": round(float(max(s.min(), q1 - 1.5 * iqr)), 2),
                "q1": round(q1, 2),
                "median": round(med, 2),
                "q3": round(q3, 2),
                "max": round(float(min(s.max(), q3 + 1.5 * iqr)), 2),
                "iqr": round(iqr, 2),
                "outliers": [round(float(v), 2) for v in s[(s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)].head(10).tolist()]
            }]
            caption = f"Five-number box plot summary of '{metric_col}' (Median: {med:.2f})."

        elif chart_type == "histogram" and metric_col in df.columns:
            s = df[metric_col].dropna()
            counts, bin_edges = np.histogram(s, bins=5)
            total = len(s)
            chart_data = [
                {
                    "bin": f"{bin_edges[i]:.2f} - {bin_edges[i+1]:.2f}",
                    "count": int(counts[i]),
                    "percentage": round((counts[i] / total * 100), 1) if total > 0 else 0.0
                }
                for i in range(len(counts))
            ]
            caption = f"5-bucket frequency distribution for '{metric_col}'."

        elif chart_type == "scatter" and request.secondary_metric_column and request.secondary_metric_column in df.columns:
            sec_metric = request.secondary_metric_column
            clean_df = df[[metric_col, sec_metric]].dropna().head(60)
            chart_data = [
                {"x": round(float(r[metric_col]), 2), "y": round(float(r[sec_metric]), 2)}
                for _, r in clean_df.iterrows()
            ]
            caption = f"Scatter distribution of {metric_col} against {sec_metric}."

        elif dim_col in date_cols:
            clean_df = df[[dim_col, metric_col]].dropna().copy()
            clean_df["period"] = pd.to_datetime(clean_df[dim_col], errors="coerce").dt.strftime("%Y-%m-%d")
            clean_df = clean_df.dropna(subset=["period"])
            
            if agg == "mean":
                grouped = clean_df.groupby("period")[metric_col].mean().reset_index()
            elif agg == "count":
                grouped = clean_df.groupby("period")[metric_col].count().reset_index()
            else:
                grouped = clean_df.groupby("period")[metric_col].sum().reset_index()

            grouped = grouped.sort_values(by="period")
            chart_data = [
                {"period": str(r["period"]), "value": round(float(r[metric_col]), 2)}
                for _, r in grouped.iterrows()
            ]
            caption = f"Temporal {agg} of '{metric_col}' across {len(chart_data)} time periods."

        else:
            clean_df = df[[dim_col, metric_col]].dropna()
            if agg == "mean":
                grouped = clean_df.groupby(dim_col)[metric_col].mean().reset_index()
            elif agg == "count":
                grouped = clean_df.groupby(dim_col)[metric_col].count().reset_index()
            else:
                grouped = clean_df.groupby(dim_col)[metric_col].sum().reset_index()

            grouped = grouped.sort_values(by=metric_col, ascending=False).head(12)
            chart_data = [
                {"category": str(r[dim_col]), "value": round(float(r[metric_col]), 2)}
                for _, r in grouped.iterrows()
            ]
            caption = f"Custom {chart_type} visual displaying '{agg}' of '{metric_col}' segmented by '{dim_col}'."

        visual_chart = VisualChart(
            id=f"custom-chart-{uuid.uuid4().hex[:8]}",
            config=VisualChartConfig(
                chart_type=chart_type,
                title=f"{agg.title()} of {metric_col.replace('_', ' ').title()} by {dim_col.replace('_', ' ').title()}" if chart_type not in ['box_plot', 'histogram'] else f"{chart_type.replace('_', ' ').title()}: {metric_col.replace('_', ' ').title()}",
                subtitle=f"Query: '{query}'" if query else f"Custom analysis of {metric_col}",
                x_axis_key="period" if dim_col in date_cols else ("column" if chart_type == "box_plot" else ("bin" if chart_type == "histogram" else "category")),
                x_axis_label=dim_col.replace('_', ' ').title(),
                y_axis_key="value" if chart_type not in ["box_plot", "histogram"] else ("median" if chart_type == "box_plot" else "count"),
                y_axis_label=f"{agg.title()} of {metric_col.replace('_', ' ').title()}",
                color_palette=palette,
                card_width="full"
            ),
            data=chart_data,
            storytelling_caption=caption
        )

        return CustomChartResponse(
            dataset_id=profile.dataset_id,
            query=request.query,
            chart=visual_chart,
            explanation=caption
        )

visualization_agent = VisualizationAgent()
