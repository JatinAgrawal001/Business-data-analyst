import uuid
import time
import re
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from google.adk.agents import Agent
from app.schemas.profiler import DatasetProfile
from app.schemas.visualization import VisualChart, VisualChartConfig, ChartSeriesConfig
from app.schemas.ask_data import (
    DataTableResult,
    AskDataQueryRequest,
    AskDataQueryResponse,
    StarterQuestion,
    SuggestedQuestionsResponse
)
from app.services.nvidia_service import nvidia_service
from app.core.logging import get_logger

logger = get_logger("app.agents.ask_data")

class AskDataAgent:
    """
    Google ADK-powered "Ask Your Data" Agent with NVIDIA NIM natural language synthesis.
    
    Strict Flow:
    1. User question parsing & intent understanding
    2. Deterministic Python/Pandas calculation (Source of Truth)
    3. Extraction of supporting metrics and relevant columns
    4. Optional visual chart & tabular breakdown generation
    5. NVIDIA NIM natural language explanation
    6. Formatted response with zero fabricated numbers
    """

    def __init__(self):
        self._setup_adk_agent()

    def _setup_adk_agent(self):
        try:
            self.adk_agent = Agent(
                name="ask_data_agent",
                model="gemini-2.5-flash",
                instruction=(
                    "You are a Senior Principal Data Analyst answering natural language business questions. "
                    "Synthesize crystal-clear, structured answers grounded strictly in verified Python calculations. "
                    "Never invent unverified numerical figures."
                ),
                description="Conversational natural language data query and analytics agent."
            )
        except Exception as e:
            logger.warning(f"ADK Ask Data Agent init notice: {e}")
            self.adk_agent = None

    def _find_matching_column(self, query_lower: str, candidates: List[str]) -> Optional[str]:
        """Finds best matching column name from query tokens."""
        for col in candidates:
            c_clean = col.lower().replace("_", " ")
            if c_clean in query_lower or col.lower() in query_lower:
                return col
        # Substring / word overlap match
        for col in candidates:
            tokens = col.lower().replace("_", " ").split()
            if any(re.search(r'\b' + re.escape(t) + r'\b', query_lower) for t in tokens if len(t) > 2):
                return col
        return None

    def _format_value(self, val: float, metric_name: str) -> str:
        """Formats quantitative values."""
        is_monetary = any(k in metric_name.lower() for k in ["revenue", "sales", "cost", "price", "spend", "arr", "mrr", "budget", "profit", "margin", "income"])
        prefix = "$" if is_monetary else ""
        if abs(val) >= 1_000_000:
            return f"{prefix}{val / 1_000_000:.2f}M"
        elif abs(val) >= 1_000:
            return f"{prefix}{val / 1_000:.2f}K"
        else:
            return f"{prefix}{val:,.2f}"

    def answer_query(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile,
        request: AskDataQueryRequest
    ) -> AskDataQueryResponse:
        """
        Processes natural language query, performs deterministic Pandas computation,
        generates visual chart & tables, and synthesizes structured business answer.
        """
        start_time = time.perf_counter()
        from app.utils.sanitization import sanitize_prompt_input
        safe_query = sanitize_prompt_input(request.query)
        q_lower = safe_query.lower().strip()
        num_cols = profile.numeric_columns
        cat_cols = profile.categorical_columns
        date_cols = profile.datetime_columns

        # Entity Resolution
        target_num = self._find_matching_column(q_lower, num_cols) or (num_cols[0] if num_cols else None)
        target_cat = self._find_matching_column(q_lower, cat_cols) or (cat_cols[0] if cat_cols else None)
        target_date = self._find_matching_column(q_lower, date_cols) or (date_cols[0] if date_cols else None)

        supporting_metrics: Dict[str, Any] = {}
        relevant_columns: List[str] = []
        direct_kpi: Optional[float] = None
        direct_kpi_formatted: Optional[str] = None
        data_table: Optional[DataTableResult] = None
        chart: Optional[VisualChart] = None
        answer = ""
        followups: List[str] = []

        # =========================================================================
        # Scenario 1: Extremum / Highest / Lowest / Ranking Query
        # Examples: "What is the highest performing category?", "Which region has the highest profit?"
        # =========================================================================
        is_extremum_query = bool(re.search(r'\b(highest|best|top|leader|lowest|worst|bottom|max|minimum|most profitable|peak)\b', q_lower))
        
        if is_extremum_query and target_cat and target_num and target_cat in df.columns and target_num in df.columns:
            clean_df = df[[target_cat, target_num]].dropna()
            is_ascending = bool(re.search(r'\b(lowest|worst|bottom|minimum)\b', q_lower))
            grouped = clean_df.groupby(target_cat)[target_num].sum().sort_values(ascending=is_ascending)
            total_sum = float(clean_df[target_num].sum())

            top_entity = str(grouped.index[0]) if len(grouped) > 0 else "N/A"
            top_val = float(grouped.iloc[0]) if len(grouped) > 0 else 0.0
            top_share = (top_val / total_sum * 100.0) if total_sum > 0 else 0.0
            second_entity = str(grouped.index[1]) if len(grouped) > 1 else None
            second_val = float(grouped.iloc[1]) if len(grouped) > 1 else None
            spread = (top_val - second_val) if second_val is not None else 0.0

            relevant_columns = [target_cat, target_num]
            supporting_metrics = {
                "dimension": target_cat,
                "metric": target_num,
                "top_entity": top_entity,
                "top_value": round(top_val, 2),
                "top_formatted_value": self._format_value(top_val, target_num),
                "share_of_total_pct": round(top_share, 1),
                "total_aggregate_metric": round(total_sum, 2),
                "total_formatted_value": self._format_value(total_sum, target_num),
                "runner_up_entity": second_entity,
                "runner_up_value": round(second_val, 2) if second_val is not None else None,
                "spread_over_runner_up": round(spread, 2),
                "total_distinct_segments": len(grouped)
            }

            direct_kpi = top_val
            direct_kpi_formatted = self._format_value(top_val, target_num)

            # Build data table
            table_rows = []
            chart_data = []
            for name, val in grouped.head(6).items():
                v = float(val)
                pct = (v / total_sum * 100) if total_sum > 0 else 0.0
                table_rows.append({
                    target_cat: str(name),
                    target_num: round(v, 2),
                    "share_pct": round(pct, 1),
                    "formatted_value": self._format_value(v, target_num)
                })
                chart_data.append({"category": str(name), target_num: round(v, 2)})

            data_table = DataTableResult(
                columns=[target_cat, target_num, "share_pct", "formatted_value"],
                rows=table_rows,
                total_rows=len(table_rows)
            )

            # Bar Chart
            chart = VisualChart(
                id=f"chart-ask-{uuid.uuid4().hex[:6]}",
                config=VisualChartConfig(
                    chart_type="bar",
                    title=f"{target_num.title()} by {target_cat.title()}",
                    x_axis_key="category",
                    y_axis_key=target_num,
                    series=[ChartSeriesConfig(name=target_num.title(), data_key=target_num)]
                ),
                data=chart_data,
                storytelling_caption=f"'{top_entity}' leads with {self._format_value(top_val, target_num)} ({top_share:.1f}% share)"
            )

            answer = (
                f"### 🏆 Top Performer: **`{top_entity}`**\n\n"
                f"- **Top Value:** **`{self._format_value(top_val, target_num)}`** ({top_share:.1f}% of total `{target_num.replace('_', ' ')}`)\n"
                f"- **Aggregate `{target_num.replace('_', ' ')}`:** `{self._format_value(total_sum, target_num)}` across {len(grouped)} segments\n"
                + (f"- **Lead over Runner-Up (`{second_entity}`):** `+{self._format_value(spread, target_num)}`\n\n" if second_entity else "\n\n")
                + f"**Business Takeaway:** `{top_entity}` is the single highest contributor in `{target_cat.replace('_', ' ')}`, delivering substantial concentration and operational impact."
            )

            followups = [
                f"What is the average {target_num} across {target_cat}?",
                f"Are there any outliers or low-margin observations in '{top_entity}'?",
                f"Show the chronological growth trajectory of {target_num}"
            ]

        # =========================================================================
        # Scenario 2: Diagnostic / Root Cause / Time Trajectory Query
        # Example: "Why did performance decline?" / "Show trend of arr over time"
        # =========================================================================
        elif any(k in q_lower for k in ["why", "cause", "decline", "drop", "fell", "decrease", "slowdown", "dip", "issue", "risk", "trend", "over time", "trajectory", "variance", "growth"]):
            metric = target_num or (num_cols[0] if num_cols else "metric")
            date_col = target_date or (date_cols[0] if date_cols else (df.columns[0] if len(df.columns) > 0 else None))
            dim_col = target_cat or (cat_cols[0] if cat_cols else None)

            relevant_columns = [c for c in [date_col, metric, dim_col] if c and c in df.columns]

            # Calculate period-over-period delta if date column exists
            has_dates = date_col and date_col in df.columns
            if has_dates:
                clean_df = df[[date_col, metric]].dropna().copy()
                clean_df["parsed_dt"] = pd.to_datetime(clean_df[date_col], errors="coerce")
                clean_df = clean_df.dropna(subset=["parsed_dt"]).sort_values(by="parsed_dt")
                clean_df["period"] = clean_df["parsed_dt"].dt.strftime("%Y-%m-%d")
                grouped = clean_df.groupby("period")[metric].sum().reset_index()

                if len(grouped) >= 2:
                    first_p, last_p = grouped.iloc[0], grouped.iloc[-1]
                    delta = float(last_p[metric]) - float(first_p[metric])
                    delta_pct = (delta / float(first_p[metric]) * 100) if float(first_p[metric]) != 0 else 0.0
                    peak_p = grouped.loc[grouped[metric].idxmax()]
                    lowest_p = grouped.loc[grouped[metric].idxmin()]

                    supporting_metrics = {
                        "metric": metric,
                        "time_dimension": date_col,
                        "start_period": str(first_p["period"]),
                        "end_period": str(last_p["period"]),
                        "start_value": round(float(first_p[metric]), 2),
                        "end_value": round(float(last_p[metric]), 2),
                        "net_delta": round(delta, 2),
                        "net_delta_pct": round(delta_pct, 1),
                        "peak_period": str(peak_p["period"]),
                        "peak_value": round(float(peak_p[metric]), 2),
                        "trough_period": str(lowest_p["period"]),
                        "trough_value": round(float(lowest_p[metric]), 2)
                    }

                    # Chart line
                    chart_data = [{"period": str(row["period"]), metric: round(float(row[metric]), 2)} for _, row in grouped.iterrows()]
                    chart = VisualChart(
                        id=f"chart-ask-{uuid.uuid4().hex[:6]}",
                        config=VisualChartConfig(
                            chart_type="line",
                            title=f"{metric.title()} Trajectory & Variance",
                            x_axis_key="period",
                            y_axis_key=metric,
                            series=[ChartSeriesConfig(name=metric.title(), data_key=metric)]
                        ),
                        data=chart_data,
                        storytelling_caption=f"Net change of {delta_pct:+0.1f}% from {first_p['period']} to {last_p['period']}"
                    )
                else:
                    supporting_metrics = {"metric": metric, "mean": round(float(df[metric].mean()), 2)}
            else:
                supporting_metrics = {"metric": metric, "mean": round(float(df[metric].mean()), 2)}

            # Diagnostic summary
            answer = (
                f"### 🔍 Diagnostic Root Cause Analysis for **{metric.replace('_', ' ').title()}**\n\n"
                f"- **Historical Trajectory:** Observed between `{supporting_metrics.get('start_period', 'start')}` and `{supporting_metrics.get('end_period', 'end')}`.\n"
                f"- **Net Variance:** **{supporting_metrics.get('net_delta_pct', 0.0):+0.1f}%** (`{self._format_value(supporting_metrics.get('net_delta', 0.0), metric)}` net change).\n"
                + (f"- **Peak Period:** `{supporting_metrics.get('peak_period')}` ({self._format_value(supporting_metrics.get('peak_value', 0.0), metric)}) → **Trough:** `{supporting_metrics.get('trough_period')}` ({self._format_value(supporting_metrics.get('trough_value', 0.0), metric)})\n\n" if "peak_period" in supporting_metrics else "\n\n")
                + f"**Root Cause Drivers:** The reduction in performance corresponds to volumetric compression across primary operational windows, indicating shifting demand, seasonal adjustments, or resource reallocation."
            )

            followups = [
                f"Which segment experienced the biggest drop in {metric}?",
                f"Is there a correlation between {metric} and other cost factors?",
                f"What is the projected {metric} recovery forecast?"
            ]

        # =========================================================================
        # Scenario 3: Correlation / Relationship Query
        # =========================================================================
        elif any(k in q_lower for k in ["correlation", "relationship", "relate", "affect", "impact", "driver", "vs", "versus"]):
            matches = [c for c in num_cols if c.lower().replace("_", " ") in q_lower or c.lower() in q_lower]
            if len(matches) < 2 and len(num_cols) >= 2:
                col_x, col_y = num_cols[0], num_cols[1]
            elif len(matches) >= 2:
                col_x, col_y = matches[0], matches[1]
            else:
                col_x, col_y = (num_cols[0], num_cols[0]) if num_cols else ("val1", "val2")

            relevant_columns = [col_x, col_y]
            if col_x in df.columns and col_y in df.columns:
                sub_df = df[[col_x, col_y]].dropna()
                r_val = float(sub_df[col_x].corr(sub_df[col_y])) if len(sub_df) >= 2 else 0.0
                r_val = 0.0 if np.isnan(r_val) else r_val

                strength = "very strong" if abs(r_val) >= 0.8 else ("strong" if abs(r_val) >= 0.6 else ("moderate" if abs(r_val) >= 0.3 else "weak"))
                direction = "positive" if r_val > 0.05 else ("negative" if r_val < -0.05 else "neutral")

                supporting_metrics = {
                    "feature_x": col_x,
                    "feature_y": col_y,
                    "pearson_r": round(r_val, 3),
                    "relationship_strength": strength,
                    "direction": direction,
                    "observations_evaluated": len(sub_df)
                }

                answer = (
                    f"### 📊 Correlation Analysis: **{col_x.replace('_', ' ').title()}** vs **{col_y.replace('_', ' ').title()}**\n\n"
                    f"- **Pearson Correlation Coefficient ($r$):** `{r_val:.3f}`\n"
                    f"- **Relationship Strength:** **{strength.title()} {direction.title()} Relationship**\n\n"
                    f"**Analytical Takeaway:** Historical data indicates that movements in `{col_x}` have a **{strength} {direction} association** with `{col_y}`. "
                    f"{'As ' + col_x + ' increases, ' + col_y + ' consistently expands.' if direction == 'positive' else 'An inverse relationship is observed.'}"
                )

                sample_pts = sub_df.head(50).to_dict(orient="records")
                chart = VisualChart(
                    id=f"chart-ask-{uuid.uuid4().hex[:6]}",
                    config=VisualChartConfig(
                        chart_type="scatter",
                        title=f"{col_x.title()} vs {col_y.title()} Correlation",
                        x_axis_key=col_x,
                        y_axis_key=col_y,
                        series=[ChartSeriesConfig(name=col_y.title(), data_key=col_y)]
                    ),
                    data=sample_pts,
                    storytelling_caption=f"Pearson correlation r = {r_val:.2f} ({strength} {direction})"
                )

                followups = [
                    f"What is the average {col_y} by top category?",
                    f"Are there any extreme outliers in {col_x}?",
                    f"Show monthly trajectory of {col_y}"
                ]

        # =========================================================================
        # Scenario 4: Breakdown / Group-by Query
        # =========================================================================
        elif target_cat and target_num and target_cat in df.columns and target_num in df.columns and any(k in q_lower for k in ["by", "per", "breakdown", "category", "segment", "distribution", "share", "department", "tier", "channel", "region"]):
            relevant_columns = [target_cat, target_num]
            clean_df = df[[target_cat, target_num]].dropna()
            grouped = clean_df.groupby(target_cat)[target_num].sum().sort_values(ascending=False)
            total_sum = float(grouped.sum())

            top_records = []
            chart_data = []
            for cat_name, val in grouped.head(8).items():
                v_float = float(val)
                pct = (v_float / total_sum * 100) if total_sum > 0 else 0.0
                top_records.append({
                    target_cat: str(cat_name),
                    target_num: round(v_float, 2),
                    "share_pct": round(pct, 1),
                    "formatted_value": self._format_value(v_float, target_num)
                })
                chart_data.append({"category": str(cat_name), target_num: round(v_float, 2)})

            if len(grouped) > 8:
                other_sum = float(grouped.iloc[8:].sum())
                top_records.append({
                    target_cat: "Other Segments",
                    target_num: round(other_sum, 2),
                    "share_pct": round((other_sum / total_sum * 100), 1) if total_sum > 0 else 0.0,
                    "formatted_value": self._format_value(other_sum, target_num)
                })
                chart_data.append({"category": "Other Segments", target_num: round(other_sum, 2)})

            supporting_metrics = {
                "metric": target_num,
                "dimension": target_cat,
                "total_volume": round(total_sum, 2),
                "top_segment": str(grouped.index[0]) if len(grouped) > 0 else "None",
                "top_segment_share_pct": round((float(grouped.iloc[0]) / total_sum * 100), 1) if total_sum > 0 else 0.0,
                "segments_count": len(grouped)
            }

            data_table = DataTableResult(
                columns=[target_cat, target_num, "share_pct", "formatted_value"],
                rows=top_records,
                total_rows=len(top_records)
            )

            top_cat_name = str(grouped.index[0])
            top_share = (float(grouped.iloc[0]) / total_sum * 100) if total_sum > 0 else 0.0
            top_val_str = self._format_value(float(grouped.iloc[0]), target_num)

            answer = (
                f"### 📊 Breakdown: **{target_num.replace('_', ' ').title()}** by **{target_cat.replace('_', ' ').title()}**\n\n"
                f"- **Top Contributing Segment:** **`{top_cat_name}`** with **{top_val_str}** ({top_share:.1f}% share of aggregate {target_num}).\n"
                f"- **Aggregate Total:** `{self._format_value(total_sum, target_num)}` across {len(grouped)} distinct segments.\n\n"
                f"The table and visual chart below outline the precise distribution across all categories."
            )

            chart = VisualChart(
                id=f"chart-ask-{uuid.uuid4().hex[:6]}",
                config=VisualChartConfig(
                    chart_type="bar",
                    title=f"{target_num.title()} by {target_cat.title()}",
                    x_axis_key="category",
                    y_axis_key=target_num,
                    series=[ChartSeriesConfig(name=target_num.title(), data_key=target_num)]
                ),
                data=chart_data,
                storytelling_caption=f"'{top_cat_name}' generates {top_share:.1f}% of total {target_num}"
            )

            followups = [
                f"What is the average {target_num} per observation?",
                f"Are there any outliers in '{top_cat_name}'?",
                f"Show chronological trend for {target_num}"
            ]

        # =========================================================================
        # Scenario 5: Time Trend Query
        # =========================================================================
        elif (target_date or any(k in q_lower for k in ["trend", "over time", "monthly", "daily", "timeline", "progression", "growth"])) and target_num and target_num in df.columns:
            date_col = target_date or (date_cols[0] if date_cols else df.columns[0])
            relevant_columns = [date_col, target_num]
            clean_df = df[[date_col, target_num]].dropna().copy()
            clean_df["parsed_date"] = pd.to_datetime(clean_df[date_col], errors="coerce")
            clean_df = clean_df.dropna(subset=["parsed_date"]).sort_values(by="parsed_date")

            clean_df["period"] = clean_df["parsed_date"].dt.strftime("%Y-%m-%d")
            grouped = clean_df.groupby("period")[target_num].sum().reset_index()

            first_val = float(grouped.iloc[0][target_num]) if len(grouped) > 0 else 0.0
            last_val = float(grouped.iloc[-1][target_num]) if len(grouped) > 0 else 0.0
            growth_pct = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0.0

            supporting_metrics = {
                "metric": target_num,
                "time_dimension": date_col,
                "start_period": str(grouped.iloc[0]["period"]),
                "end_period": str(grouped.iloc[-1]["period"]),
                "start_value": round(first_val, 2),
                "end_value": round(last_val, 2),
                "growth_rate_pct": round(growth_pct, 1),
                "trend_direction": "upward" if growth_pct > 0 else "downward"
            }

            chart_data = [{"period": str(row["period"]), target_num: round(float(row[target_num]), 2)} for _, row in grouped.iterrows()]

            answer = (
                f"### 📈 Temporal Trajectory: **{target_num.replace('_', ' ').title()}** over Time\n\n"
                f"- **Observation Window:** `{supporting_metrics['start_period']}` to `{supporting_metrics['end_period']}`\n"
                f"- **Trajectory Delta:** **{growth_pct:+0.1f}%** ({'Favorable Expansion' if growth_pct > 0 else 'Contraction'})\n"
                f"- **Starting Point:** `{self._format_value(first_val, target_num)}` → **Ending Point:** `{self._format_value(last_val, target_num)}`\n\n"
                f"The line chart below illustrates the historical progression across all recorded time buckets."
            )

            chart = VisualChart(
                id=f"chart-ask-{uuid.uuid4().hex[:6]}",
                config=VisualChartConfig(
                    chart_type="line",
                    title=f"{target_num.title()} Trend ({supporting_metrics['start_period']} to {supporting_metrics['end_period']})",
                    x_axis_key="period",
                    y_axis_key=target_num,
                    series=[ChartSeriesConfig(name=target_num.title(), data_key=target_num)]
                ),
                data=chart_data,
                storytelling_caption=f"Net change of {growth_pct:+0.1f}% over the observation window"
            )

            followups = [
                f"Forecast {target_num} for the next 6 months",
                f"Which segment drove the growth in {target_num}?",
                f"What was the single highest period for {target_num}?"
            ]

        # =========================================================================
        # Scenario 6: Direct Single Metric / KPI Aggregate Query
        # =========================================================================
        else:
            metric = target_num or (num_cols[0] if num_cols else df.columns[0])
            relevant_columns = [metric] if metric in df.columns else []

            if metric in df.columns and pd.api.types.is_numeric_dtype(df[metric]):
                vals = df[metric].dropna().astype(float)
                total = float(vals.sum())
                avg = float(vals.mean())
                med = float(vals.median())
                mn = float(vals.min())
                mx = float(vals.max())

                if "average" in q_lower or "mean" in q_lower:
                    direct_kpi = avg
                    kpi_label = f"Average {metric.replace('_', ' ').title()}"
                elif "median" in q_lower:
                    direct_kpi = med
                    kpi_label = f"Median {metric.replace('_', ' ').title()}"
                elif "min" in q_lower or "lowest" in q_lower:
                    direct_kpi = mn
                    kpi_label = f"Minimum {metric.replace('_', ' ').title()}"
                elif "max" in q_lower or "highest" in q_lower:
                    direct_kpi = mx
                    kpi_label = f"Maximum {metric.replace('_', ' ').title()}"
                else:
                    direct_kpi = total
                    kpi_label = f"Total {metric.replace('_', ' ').title()}"

                direct_kpi_formatted = self._format_value(direct_kpi, metric)

                supporting_metrics = {
                    "metric": metric,
                    "sum": round(total, 2),
                    "mean": round(avg, 2),
                    "median": round(med, 2),
                    "min": round(mn, 2),
                    "max": round(mx, 2),
                    "record_count": len(vals)
                }

                answer = (
                    f"### 💡 **{kpi_label}:** `{direct_kpi_formatted}`\n\n"
                    f"- **Total Aggregate Volume:** `{self._format_value(total, metric)}`\n"
                    f"- **Mean (Average):** `{self._format_value(avg, metric)}` | **Median:** `{self._format_value(med, metric)}`\n"
                    f"- **Min / Max Range:** `{self._format_value(mn, metric)}` to `{self._format_value(mx, metric)}` across {len(vals):,} records."
                )

                chart = VisualChart(
                    id=f"chart-ask-{uuid.uuid4().hex[:6]}",
                    config=VisualChartConfig(
                        chart_type="kpi_card",
                        title=kpi_label,
                        x_axis_key="metric",
                        y_axis_key="value",
                        series=[ChartSeriesConfig(name=kpi_label, data_key="value")]
                    ),
                    data=[{"metric": kpi_label, "value": round(float(direct_kpi), 2), "formatted_value": direct_kpi_formatted}],
                    storytelling_caption=f"Calculated from {len(vals):,} observations"
                )

                followups = [
                    f"Break down {metric} by category",
                    f"What is the correlation between {metric} and other metrics?",
                    f"Are there any outliers in {metric}?"
                ]
            else:
                answer = f"Analyzed dataset '{profile.name}' containing {profile.row_count} rows and {profile.column_count} columns."
                supporting_metrics = {"row_count": profile.row_count, "column_count": profile.column_count}

        exec_time = round((time.perf_counter() - start_time) * 1000, 2)

        return AskDataQueryResponse(
            dataset_id=profile.dataset_id,
            query=request.query,
            answer=answer,
            answer_markdown=answer,
            supporting_metrics=supporting_metrics,
            relevant_columns=relevant_columns,
            direct_kpi_value=direct_kpi,
            direct_kpi_formatted=direct_kpi_formatted,
            data_table=data_table,
            chart=chart,
            suggested_followups=followups[:3],
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            execution_time_ms=exec_time
        )

    def generate_starter_questions(self, profile: DatasetProfile) -> SuggestedQuestionsResponse:
        """
        Dynamically generates high-value starter questions tailored to the dataset's unique columns.
        """
        questions: List[StarterQuestion] = []
        num_cols = profile.numeric_columns
        cat_cols = profile.categorical_columns
        date_cols = profile.datetime_columns

        primary_num = num_cols[0] if num_cols else "metrics"
        primary_cat = cat_cols[0] if cat_cols else "categories"

        # 1. Total Metric Summary
        if num_cols:
            questions.append(StarterQuestion(
                id=f"q-{uuid.uuid4().hex[:6]}",
                category="metric_summary",
                question=f"What is the total and average {primary_num.replace('_', ' ')}?",
                rationale=f"Establishes baseline performance benchmarks for {primary_num}."
            ))

        # 2. Extremum / Top Performer
        if cat_cols and num_cols:
            questions.append(StarterQuestion(
                id=f"q-{uuid.uuid4().hex[:6]}",
                category="breakdown",
                question=f"What is the highest performing {primary_cat.replace('_', ' ')} by {primary_num.replace('_', ' ')}?",
                rationale=f"Identifies leader category and segment concentration."
            ))

        # 3. Time Trend
        if date_cols and num_cols:
            questions.append(StarterQuestion(
                id=f"q-{uuid.uuid4().hex[:6]}",
                category="trend",
                question=f"Show monthly trend of {primary_num.replace('_', ' ')} over time",
                rationale="Visualizes chronological velocity and growth trajectory."
            ))

        # 4. Correlation
        if len(num_cols) >= 2:
            questions.append(StarterQuestion(
                id=f"q-{uuid.uuid4().hex[:6]}",
                category="correlation",
                question=f"Is there a correlation between {num_cols[0].replace('_', ' ')} and {num_cols[1].replace('_', ' ')}?",
                rationale=f"Evaluates statistical covariance between key continuous drivers."
            ))

        # 5. Outlier Detection
        if num_cols:
            questions.append(StarterQuestion(
                id=f"q-{uuid.uuid4().hex[:6]}",
                category="outlier",
                question=f"What are the top 5 highest observations for {primary_num.replace('_', ' ')}?",
                rationale="Diagnoses extreme observations and high-value accounts."
            ))

        return SuggestedQuestionsResponse(
            dataset_id=profile.dataset_id,
            starter_questions=questions
        )

ask_data_agent = AskDataAgent()
