import io
import uuid
import json
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timezone

from google.adk.agents import Agent
from app.schemas.profiler import DatasetProfile
from app.schemas.eda import EDAReport
from app.schemas.insight import StructuredInsightReport
from app.schemas.recommendation import RecommendationReport
from app.schemas.prediction import PredictionReport
from app.schemas.report import (
    ExecutiveReport,
    ReportSection,
    GenerateReportRequest,
    ReportExportResponse
)
from app.agents.eda_agent import eda_agent
from app.agents.visualization_agent import visualization_agent
from app.agents.insight_agent import insight_agent
from app.agents.recommendation_agent import recommendation_agent
from app.agents.prediction_agent import prediction_agent
from app.core.nvidia_client import NvidiaClient
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("app.agents.report")

class ReportAgent:
    """
    Comprehensive Executive Report Generation Agent.
    
    Ensures every report contains the 10 mandatory sections based strictly on actual calculations:
    1. Executive Summary
    2. Dataset Overview
    3. Data Quality
    4. KPIs
    5. Important Charts
    6. Key Insights
    7. Risks
    8. Recommendations
    9. Forecast when available
    10. Limitations
    
    Outputs:
    - Downloadable PDF (via ReportLab)
    - Standalone Dark/Printable HTML
    - Structured Markdown
    - Typed JSON API objects
    """

    def __init__(self):
        self._setup_adk_agent()
        self.nvidia_client = NvidiaClient()

    def _setup_adk_agent(self):
        try:
            self.adk_agent = Agent(
                name="report_agent",
                model="gemini-2.5-flash",
                instruction=(
                    "You are a Chief Strategy & Business Intelligence Officer. "
                    "Synthesize high-impact executive intelligence reports combining empirical data facts, "
                    "strategic priorities, and probabilistic forecasts into concise executive language. "
                    "Never fabricate or alter numerical figures."
                ),
                description="Generates executive intelligence reports, memos, and multi-format exports."
            )
        except Exception as e:
            logger.warning(f"ADK Report Agent init notice: {e}")
            self.adk_agent = None

    def generate_report(
        self,
        df: pd.DataFrame,
        profile: DatasetProfile,
        request: GenerateReportRequest,
        author: str = "Lead Business Intelligence Analyst"
    ) -> ExecutiveReport:
        """
        Synthesizes a complete Executive Intelligence Report strictly adhering to the 10 core sections.
        """
        report_id = f"rep-{uuid.uuid4().hex[:8]}"
        title = request.title or f"{profile.name} - Executive Intelligence Brief"
        subtitle = request.subtitle or f"Comprehensive statistical profiling and strategic forecast compiled on {datetime.now(timezone.utc).strftime('%B %d, %Y')}"

        # Run underlying analytical engines
        eda_report = eda_agent.generate_eda_report(df, profile)
        insight_report = insight_agent.generate_report(df, profile, eda_report)
        rec_report = recommendation_agent.generate_report(df, profile, eda_report, insight_report)
        pred_report = prediction_agent.generate_report(df, profile, forecast_horizon=6)
        viz_dashboard = visualization_agent.generate_dashboard(df, profile)

        sections: List[ReportSection] = []

        # =========================================================================
        # 1. EXECUTIVE SUMMARY
        # =========================================================================
        primary_metric = profile.numeric_columns[0] if profile.numeric_columns else "records"
        primary_dim = profile.categorical_columns[0] if profile.categorical_columns else "dimensions"
        upside_str = rec_report.estimated_total_upside or "High Strategic Value"

        exec_summary_text = (
            f"Executive intelligence synthesis for **{profile.name}**. Evaluated **{profile.row_count:,} observations** "
            f"across **{profile.column_count} dimensions** ({len(profile.numeric_columns)} numeric metrics, "
            f"{len(profile.categorical_columns)} categorical segments, {len(profile.datetime_columns)} temporal axes). "
            f"Overall dataset health is rated at **{profile.quality_report.health_score:.1f}/100** with "
            f"**{profile.quality_report.complete_rows_percentage:.1f}% complete observations**.\n\n"
            f"Analysis surfaced **{insight_report.total_insights} grounded empirical insights**, **{len(insight_report.risks) + len(insight_report.anomalies)} risk factors**, "
            f"and **{len(rec_report.recommendations)} prioritized strategic initiatives** with an estimated modeled uplift of **{upside_str}**. "
            f"Predictive modeling champion: **{pred_report.primary_forecast.model_used if (pred_report.is_suitable and pred_report.primary_forecast) else 'Forecasting paused (non-temporal / insufficient history)'}**."
        )
        sections.append(ReportSection(
            id="sec-1-exec-summary",
            title="1. Executive Summary",
            type="executive_summary",
            content=exec_summary_text
        ))

        # =========================================================================
        # 2. DATASET OVERVIEW
        # =========================================================================
        overview_payload = {
            "dataset_name": profile.name,
            "file_type": profile.file_type.upper(),
            "total_rows": profile.row_count,
            "total_columns": profile.column_count,
            "memory_usage_kb": round(profile.quality_report.memory_usage_bytes / 1024, 1),
            "numeric_columns_count": len(profile.numeric_columns),
            "categorical_columns_count": len(profile.categorical_columns),
            "datetime_columns_count": len(profile.datetime_columns),
            "numeric_columns": [
                {
                    "name": c.name,
                    "min": c.numeric_stats.min if c.numeric_stats else None,
                    "max": c.numeric_stats.max if c.numeric_stats else None,
                    "mean": c.numeric_stats.mean if c.numeric_stats else None,
                    "sum": c.numeric_stats.sum if c.numeric_stats else None
                }
                for c in profile.columns if c.data_type == "numeric" and c.numeric_stats
            ],
            "categorical_columns": [
                {
                    "name": c.name,
                    "cardinality": c.categorical_stats.cardinality if c.categorical_stats else None,
                    "distinct_ratio": c.categorical_stats.distinct_ratio if c.categorical_stats else None,
                    "mode": c.categorical_stats.mode if c.categorical_stats else None
                }
                for c in profile.columns if c.data_type == "categorical" and c.categorical_stats
            ],
            "datetime_columns": [
                {
                    "name": c.name,
                    "min_date": c.datetime_stats.min_date if c.datetime_stats else None,
                    "max_date": c.datetime_stats.max_date if c.datetime_stats else None,
                    "timespan_days": c.datetime_stats.timespan_days if c.datetime_stats else None
                }
                for c in profile.columns if c.data_type == "datetime" and c.datetime_stats
            ]
        }
        sections.append(ReportSection(
            id="sec-2-dataset-overview",
            title="2. Dataset Overview",
            type="dataset_overview",
            content=overview_payload
        ))

        # =========================================================================
        # 3. DATA QUALITY
        # =========================================================================
        quality_payload = {
            "health_score": profile.quality_report.health_score,
            "total_cells": profile.quality_report.total_cells,
            "missing_cells": profile.quality_report.missing_cells,
            "missing_percentage": profile.quality_report.missing_percentage,
            "complete_rows_count": profile.quality_report.complete_rows_count,
            "complete_rows_percentage": profile.quality_report.complete_rows_percentage,
            "duplicate_rows_count": profile.quality_report.duplicate_rows_count,
            "duplicate_rows_percentage": profile.quality_report.duplicate_rows_percentage,
            "warnings": [w.model_dump() for w in profile.quality_report.warnings]
        }
        sections.append(ReportSection(
            id="sec-3-data-quality",
            title="3. Data Quality & Hygiene Assessment",
            type="data_quality",
            content=quality_payload
        ))

        # =========================================================================
        # 4. KEY PERFORMANCE INDICATORS (KPIs)
        # =========================================================================
        sections.append(ReportSection(
            id="sec-4-kpis",
            title="4. Key Performance Indicators",
            type="kpi_grid",
            content=[k.model_dump() for k in eda_report.kpis]
        ))

        # =========================================================================
        # 5. IMPORTANT CHARTS
        # =========================================================================
        sections.append(ReportSection(
            id="sec-5-charts",
            title="5. Visual Trajectories & Dimensional Distributions",
            type="chart_view",
            content=[c.model_dump() for c in viz_dashboard.charts]
        ))

        # =========================================================================
        # 6. KEY INSIGHTS
        # =========================================================================
        top_insights = (insight_report.key_insights + insight_report.trends + insight_report.opportunities)
        sections.append(ReportSection(
            id="sec-6-key-insights",
            title="6. Grounded Statistical Insights & Growth Opportunities",
            type="key_insights",
            content=[ins.model_dump() for ins in top_insights]
        ))

        # =========================================================================
        # 7. RISKS & ANOMALIES
        # =========================================================================
        risks_and_anomalies = (insight_report.risks + insight_report.anomalies)
        sections.append(ReportSection(
            id="sec-7-risks",
            title="7. Risk Factors & Empirical Anomalies",
            type="risks_list",
            content=[r.model_dump() for r in risks_and_anomalies]
        ))

        # =========================================================================
        # 8. RECOMMENDATIONS (6-PILLAR FRAMEWORK)
        # =========================================================================
        sections.append(ReportSection(
            id="sec-8-recommendations",
            title="8. Prioritized Strategic Recommendations (6-Pillar Framework)",
            type="recommendations_table",
            content=[r.model_dump() for r in rec_report.recommendations]
        ))

        # =========================================================================
        # 9. FORECAST WHEN AVAILABLE
        # =========================================================================
        if pred_report.is_suitable and pred_report.primary_forecast:
            forecast_content = pred_report.primary_forecast.model_dump()
            forecast_content["is_suitable"] = True
            forecast_content["suitability_notes"] = "Validated historical temporal consistency and stationary frequency."
        else:
            unsuitable_reasons = (
                pred_report.suitability_report.unsuitability_reasons
                if pred_report.suitability_report
                else ["Dataset lacks sequential timestamp dimension or sufficient observations."]
            )
            forecast_content = {
                "is_suitable": False,
                "target_metric": primary_metric,
                "model_used": "Forecasting Inappropriate",
                "projected_net_change_pct": 0.0,
                "predicted_values": [],
                "unsuitability_reasons": unsuitable_reasons,
                "natural_language_summary": (
                    f"Time-series forecasting is mathematically inappropriate for '{profile.name}'. "
                    f"Reason: {'; '.join(unsuitable_reasons)}. "
                    "Rather than producing an ungrounded hallucination, prediction modeling was intentionally skipped."
                ),
                "remediation_guidance": "Include a standardized sequential date column with at least 5-10 regular intervals."
            }

        sections.append(ReportSection(
            id="sec-9-forecast",
            title="9. Predictive Horizon & Driver Sensitivity",
            type="forecast_view",
            content=forecast_content
        ))

        # =========================================================================
        # 10. LIMITATIONS & METHODOLOGY
        # =========================================================================
        limitations_text = (
            f"1. **Sample Scope**: Analysis is bounded to {profile.row_count:,} records in '{profile.name}'. "
            f"Unobserved external variables or confounding macroeconomic shifts may influence empirical stability.\n"
            f"2. **Causality Boundary**: Correlation coefficients ($r$) establish empirical association but do not prove direct causality.\n"
            f"3. **Predictive Horizon**: Forward projections are probabilistic mathematical models based on historical patterns and do not guarantee business results.\n"
            f"4. **Data Hygiene**: Metrics reflect reported records; missing data was evaluated under strict non-imputing determinism."
        )
        sections.append(ReportSection(
            id="sec-10-limitations",
            title="10. Analytical Limitations & Governance Methodology",
            type="limitations_view",
            content=limitations_text
        ))

        # Key Takeaways
        key_takeaways = [
            f"Data Integrity: Rated {profile.quality_report.health_score:.1f}/100 with {profile.quality_report.complete_rows_percentage:.1f}% row completeness.",
            f"Primary Driver: '{insight_report.key_insights[0].headline}'" if insight_report.key_insights else f"Primary volume concentrated in {primary_metric}.",
            f"Priority Action: '{rec_report.recommendations[0].title}' targeted to capture {rec_report.recommendations[0].formatted_impact}." if rec_report.recommendations else "Maintain continuous metric tracking.",
            f"Forward Outlook: Projected {pred_report.primary_forecast.projected_net_change_pct:+.1f}% net change." if (pred_report.is_suitable and pred_report.primary_forecast) else "Forecasting paused (non-temporal dataset)."
        ]

        return ExecutiveReport(
            id=report_id,
            project_id=profile.project_id,
            dataset_id=profile.dataset_id,
            dataset_name=profile.name,
            title=title,
            subtitle=subtitle,
            executive_summary=exec_summary_text,
            key_takeaways=key_takeaways,
            sections=sections,
            author=author,
            status="published",
            format="pdf",
            cadence=request.cadence,
            generated_at=datetime.now(timezone.utc).isoformat(),
            disclaimer=(
                "All statistical figures, insights, and predictive trajectories are computed deterministically via Python analytics. "
                "Forward projections represent mathematical models and do not guarantee business results."
            )
        )

    def export_to_markdown(self, report: ExecutiveReport) -> str:
        """
        Exports all 10 report sections into a publication-grade GitHub Markdown brief.
        """
        md = []
        md.append(f"# {report.title}\n")
        md.append(f"**{report.subtitle}**\n")
        md.append(f"- **Author:** {report.author}")
        md.append(f"- **Dataset:** `{report.dataset_name}` (`{report.dataset_id}`)")
        md.append(f"- **Compiled At:** {report.generated_at}")
        md.append(f"- **Cadence:** {report.cadence.replace('_', ' ').title()}\n")
        md.append("---\n")

        md.append("## 📌 Executive Summary\n")
        md.append(f"{report.executive_summary}\n")

        md.append("### 🎯 Key Takeaways\n")
        for t in report.key_takeaways:
            md.append(f"- {t}")
        md.append("\n---\n")

        for sec in report.sections:
            md.append(f"## {sec.title}\n")

            if sec.type == "dataset_overview" and isinstance(sec.content, dict):
                ov = sec.content
                md.append(f"- **Total Rows:** `{ov.get('total_rows', 0):,}`")
                md.append(f"- **Total Columns:** `{ov.get('total_columns', 0)}`")
                md.append(f"- **Memory Footprint:** `{ov.get('memory_usage_kb', 0)} KB`")
                md.append(f"- **Dimensions:** {ov.get('numeric_columns_count', 0)} Numeric, {ov.get('categorical_columns_count', 0)} Categorical, {ov.get('datetime_columns_count', 0)} Temporal\n")

            elif sec.type == "data_quality" and isinstance(sec.content, dict):
                dq = sec.content
                md.append(f"- **Health Rating:** `{dq.get('health_score', 0):.1f} / 100`")
                md.append(f"- **Complete Rows Rate:** `{dq.get('complete_rows_percentage', 0):.1f}%`")
                md.append(f"- **Missing Cells:** `{dq.get('missing_cells', 0):,}` ({dq.get('missing_percentage', 0):.1f}%)")
                md.append(f"- **Duplicate Rows:** `{dq.get('duplicate_rows_count', 0):,}` ({dq.get('duplicate_rows_percentage', 0):.1f}%)\n")
                if dq.get("warnings"):
                    md.append("**Quality Diagnostics:**")
                    for w in dq["warnings"]:
                        md.append(f"- `[{w.get('severity', 'info').upper()}]` {w.get('message', '')}")
                    md.append("\n")

            elif sec.type == "kpi_grid" and isinstance(sec.content, list):
                md.append("| KPI Metric Name | Current Value | Net Change | Direction | Category |")
                md.append("| :--- | :--- | :--- | :--- | :--- |")
                for kpi in sec.content:
                    name = kpi.get("metric_name") or kpi.get("label") or "Metric"
                    val = kpi.get("formatted_value") or str(kpi.get("current_value", ""))
                    chg = f"{kpi.get('change_pct', 0.0):+.1f}%"
                    trend = kpi.get("trend_direction", "neutral")
                    cat = kpi.get("category", "General")
                    md.append(f"| **{name}** | `{val}` | {chg} | {trend.title()} | {cat} |")
                md.append("\n")

            elif sec.type in ["key_insights", "insights_list"] and isinstance(sec.content, list):
                for ins in sec.content:
                    cat = ins.get("category", "insight").replace("_", " ").title()
                    title = ins.get("title", "")
                    headline = ins.get("headline", "")
                    explanation = ins.get("natural_language_explanation", "")
                    action = ins.get("recommended_action", "")
                    md.append(f"### 💡 [{cat}] {title}")
                    md.append(f"> **{headline}**\n")
                    md.append(f"{explanation}\n")
                    if action:
                        md.append(f"**Recommended Action:** {action}\n")

            elif sec.type == "risks_list" and isinstance(sec.content, list):
                for r in sec.content:
                    title = r.get("title", "Identified Risk")
                    headline = r.get("headline", "")
                    explanation = r.get("natural_language_explanation", "")
                    sev = r.get("severity", "medium").upper()
                    md.append(f"### ⚠️ [{sev}] {title}")
                    md.append(f"> {headline}\n")
                    md.append(f"{explanation}\n")

            elif sec.type == "recommendations_table" and isinstance(sec.content, list):
                for r in sec.content:
                    prio = r.get("priority", "P1_high")
                    title = r.get("title", "")
                    impact = r.get("formatted_impact", "")
                    prob = r.get("problem", "")
                    action = r.get("action", "")
                    reason = r.get("reasoning", "")
                    limits = r.get("limitations", "")
                    md.append(f"### 🚀 [{prio}] {title}")
                    md.append(f"- **Problem:** {prob}")
                    md.append(f"- **Evidence & Impact:** `{impact}`")
                    md.append(f"- **Operational Action:** {action}")
                    md.append(f"- **Reasoning:** {reason}")
                    md.append(f"- **Limitations:** {limits}\n")

            elif sec.type == "forecast_view" and isinstance(sec.content, dict):
                fc = sec.content
                if fc.get("is_suitable", True):
                    metric = fc.get("target_metric", "Metric")
                    model = fc.get("model_used", "OLS")
                    net_chg = fc.get("projected_net_change_pct", 0.0)
                    summary = fc.get("natural_language_summary", "")
                    limits = fc.get("limitations", "")
                    md.append(f"- **Target Metric:** `{metric}`")
                    md.append(f"- **Champion Model:** `{model}`")
                    md.append(f"- **Projected Net Movement:** `{net_chg:+.1f}%`\n")
                    md.append(f"{summary}\n")
                    if limits:
                        md.append(f"> *Limitations:* {limits}\n")
                else:
                    md.append(f"**Forecasting Status:** `Unavailable / Inappropriate`\n")
                    md.append(f"{fc.get('natural_language_summary', '')}\n")
                    md.append(f"**Remediation:** {fc.get('remediation_guidance', '')}\n")

            elif isinstance(sec.content, str):
                md.append(f"{sec.content}\n")

            md.append("---\n")

        md.append("### ⚖️ Compliance & Governance Disclaimer")
        md.append(f"_{report.disclaimer}_\n")
        return "\n".join(md)

    def export_to_html(self, report: ExecutiveReport) -> str:
        """
        Exports the ExecutiveReport to a standalone, responsive, dark-themed HTML document with print styles.
        """
        escaped_title = report.title.replace("<", "&lt;").replace(">", "&gt;")
        
        # Build HTML content sections
        sections_html = []
        for sec in report.sections:
            sec_html = f'<div class="card"><h2 class="sec-title">{sec.title}</h2>'
            
            if sec.type == "dataset_overview" and isinstance(sec.content, dict):
                ov = sec.content
                sec_html += f"""
                <div class="kpi-grid">
                    <div class="kpi-box"><span class="kpi-val">{ov.get('total_rows', 0):,}</span><span class="kpi-lbl">Total Records</span></div>
                    <div class="kpi-box"><span class="kpi-val">{ov.get('total_columns', 0)}</span><span class="kpi-lbl">Dimensions</span></div>
                    <div class="kpi-box"><span class="kpi-val">{ov.get('file_type', 'CSV')}</span><span class="kpi-lbl">Format</span></div>
                    <div class="kpi-box"><span class="kpi-val">{ov.get('memory_usage_kb', 0)} KB</span><span class="kpi-lbl">Memory</span></div>
                </div>
                """
            elif sec.type == "data_quality" and isinstance(sec.content, dict):
                dq = sec.content
                sec_html += f"""
                <div class="kpi-grid">
                    <div class="kpi-box"><span class="kpi-val">{dq.get('health_score', 0):.1f}/100</span><span class="kpi-lbl">Health Rating</span></div>
                    <div class="kpi-box"><span class="kpi-val">{dq.get('complete_rows_percentage', 0):.1f}%</span><span class="kpi-lbl">Complete Rows</span></div>
                    <div class="kpi-box"><span class="kpi-val">{dq.get('missing_cells', 0):,}</span><span class="kpi-lbl">Missing Cells</span></div>
                    <div class="kpi-box"><span class="kpi-val">{dq.get('duplicate_rows_count', 0):,}</span><span class="kpi-lbl">Duplicates</span></div>
                </div>
                """
            elif sec.type == "kpi_grid" and isinstance(sec.content, list):
                sec_html += '<table><thead><tr><th>Metric</th><th>Value</th><th>Net Change</th><th>Direction</th><th>Category</th></tr></thead><tbody>'
                for k in sec.content:
                    name = k.get("metric_name") or k.get("label") or "Metric"
                    val = k.get("formatted_value") or str(k.get("current_value", ""))
                    chg = f"{k.get('change_pct', 0.0):+.1f}%"
                    trend = k.get("trend_direction", "neutral").title()
                    cat = k.get("category", "General")
                    sec_html += f'<tr><td><strong>{name}</strong></td><td><code>{val}</code></td><td>{chg}</td><td>{trend}</td><td>{cat}</td></tr>'
                sec_html += '</tbody></table>'

            elif sec.type in ["key_insights", "insights_list", "risks_list"] and isinstance(sec.content, list):
                for item in sec.content:
                    headline = item.get("headline", "")
                    explanation = item.get("natural_language_explanation", "")
                    cat = item.get("category", "finding").replace("_", " ").title()
                    sec_html += f"""
                    <div class="sub-card">
                        <div class="badge">{cat}</div>
                        <h4 style="margin: 6px 0; color: #ffffff;">{item.get('title', '')}</h4>
                        <p class="highlight">{headline}</p>
                        <p style="font-size: 12px; color: #9ca3af;">{explanation}</p>
                    </div>
                    """
            elif sec.type == "recommendations_table" and isinstance(sec.content, list):
                for r in sec.content:
                    sec_html += f"""
                    <div class="sub-card">
                        <div class="badge badge-purple">{r.get('priority', 'P1_high')}</div>
                        <h4 style="margin: 6px 0; color: #ffffff;">{r.get('title', '')}</h4>
                        <p style="font-size: 12px;"><strong>Problem:</strong> {r.get('problem', '')}</p>
                        <p style="font-size: 12px;"><strong>Operational Action:</strong> {r.get('action', '')}</p>
                        <p style="font-size: 12px; color: #10b981;"><strong>Expected Impact:</strong> {r.get('formatted_impact', '')}</p>
                    </div>
                    """
            elif sec.type == "forecast_view" and isinstance(sec.content, dict):
                fc = sec.content
                if fc.get("is_suitable", True):
                    sec_html += f"""
                    <p><strong>Target Metric:</strong> {fc.get('target_metric', '')} | <strong>Model:</strong> {fc.get('model_used', 'OLS')} | <strong>Projected Net Change:</strong> {fc.get('projected_net_change_pct', 0.0):+.1f}%</p>
                    <p style="font-size: 12px; color: #9ca3af;">{fc.get('natural_language_summary', '')}</p>
                    """
                else:
                    sec_html += f"""
                    <p class="highlight">Forecasting Paused: {fc.get('natural_language_summary', '')}</p>
                    <p style="font-size: 12px; color: #9ca3af;">Remediation: {fc.get('remediation_guidance', '')}</p>
                    """
            elif isinstance(sec.content, str):
                sec_html += f'<p style="font-size: 13px; line-height: 1.6;">{sec.content}</p>'

            sec_html += '</div>'
            sections_html.append(sec_html)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped_title}</title>
    <style>
        :root {{
            --bg: #0b0f19;
            --card-bg: #111827;
            --sub-bg: rgba(255, 255, 255, 0.03);
            --border: rgba(255, 255, 255, 0.08);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --accent: #6366f1;
            --accent-light: #818cf8;
            --success: #10b981;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-primary);
            line-height: 1.6;
            margin: 0;
            padding: 32px 16px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .header-card {{
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.18), rgba(17, 24, 39, 0.98));
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 32px;
            margin-bottom: 24px;
        }}
        h1 {{ font-size: 26px; margin-top: 0; margin-bottom: 6px; color: #fff; }}
        .subtitle {{ color: var(--text-secondary); font-size: 13px; margin-bottom: 18px; }}
        .meta-bar {{
            display: flex; flex-wrap: wrap; gap: 16px; font-size: 12px;
            color: var(--accent-light); border-top: 1px solid var(--border); padding-top: 14px;
        }}
        .card {{
            background: var(--card-bg); border: 1px solid var(--border);
            border-radius: 16px; padding: 24px; margin-bottom: 20px;
        }}
        .sub-card {{
            background: var(--sub-bg); border: 1px solid var(--border);
            border-radius: 12px; padding: 14px; margin-top: 12px;
        }}
        h2.sec-title {{
            font-size: 16px; color: var(--accent-light); margin-top: 0;
            border-bottom: 1px solid var(--border); padding-bottom: 10px;
        }}
        .kpi-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-top: 12px;
        }}
        .kpi-box {{
            background: var(--sub-bg); border: 1px solid var(--border);
            border-radius: 10px; padding: 12px; text-align: center;
        }}
        .kpi-val {{ display: block; font-size: 18px; font-weight: 700; color: #fff; }}
        .kpi-lbl {{ font-size: 11px; color: var(--text-secondary); text-transform: uppercase; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 12px; }}
        th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ color: var(--text-secondary); background: rgba(255, 255, 255, 0.02); }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 10px; font-weight: 600; background: rgba(99, 102, 241, 0.2); color: var(--accent-light); }}
        .badge-purple {{ background: rgba(168, 85, 247, 0.2); color: #c084fc; }}
        .highlight {{ color: #e0e7ff; font-weight: 500; font-size: 13px; margin: 4px 0; }}
        .disclaimer {{ font-size: 11px; color: var(--text-secondary); font-style: italic; text-align: center; margin-top: 32px; }}
        .btn-print {{
            padding: 8px 16px; background: var(--accent); color: #fff; border: none; border-radius: 8px;
            font-size: 12px; font-weight: 600; cursor: pointer; float: right;
        }}
        @media print {{
            body {{ background: #fff; color: #000; padding: 0; }}
            .container {{ max-width: 100%; }}
            .header-card, .card, .sub-card {{ background: #fff; color: #000; border: 1px solid #ddd; }}
            .btn-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-card">
            <button class="btn-print" onclick="window.print()">Print / Save PDF</button>
            <h1>{escaped_title}</h1>
            <div class="subtitle">{report.subtitle}</div>
            <div class="meta-bar">
                <span>👤 <strong>Author:</strong> {report.author}</span>
                <span>📊 <strong>Dataset:</strong> {report.dataset_name}</span>
                <span>📅 <strong>Generated:</strong> {report.generated_at[:10]}</span>
            </div>
        </div>

        {"".join(sections_html)}

        <div class="disclaimer">
            {report.disclaimer}
        </div>
    </div>
</body>
</html>"""
        return html

    def export_to_pdf(self, report: ExecutiveReport) -> bytes:
        """
        Generates a standalone binary PDF document using ReportLab.
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1e1b4b")
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#4b5563")
        )
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#4338ca"),
            spaceBefore=10,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            'BodyDark',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1f2937")
        )

        elements = []

        # Header Title
        elements.append(Paragraph(report.title, title_style))
        elements.append(Paragraph(f"{report.subtitle} | Author: {report.author} | Date: {report.generated_at[:10]}", subtitle_style))
        elements.append(Spacer(1, 12))

        # Iterate all sections
        for sec in report.sections:
            elements.append(Paragraph(sec.title, heading_style))

            if sec.type == "executive_summary" and isinstance(sec.content, str):
                elements.append(Paragraph(sec.content.replace("**", ""), body_style))
                elements.append(Spacer(1, 8))

            elif sec.type == "kpi_grid" and isinstance(sec.content, list):
                table_data = [["Metric Name", "Value", "Net Change", "Trend", "Category"]]
                for k in sec.content[:8]:
                    name = k.get("metric_name") or k.get("label") or "Metric"
                    val = k.get("formatted_value") or str(k.get("current_value", ""))
                    chg = f"{k.get('change_pct', 0.0):+.1f}%"
                    trend = k.get("trend_direction", "neutral").title()
                    cat = k.get("category", "General")
                    table_data.append([name, val, chg, trend, cat])

                t = Table(table_data, colWidths=[140, 90, 80, 80, 110])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e0e7ff")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1e1b4b")),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ]))
                elements.append(t)
                elements.append(Spacer(1, 8))

            elif sec.type == "recommendations_table" and isinstance(sec.content, list):
                for r in sec.content[:4]:
                    prio = r.get("priority", "P1_high")
                    title = r.get("title", "")
                    action = r.get("action", "")
                    impact = r.get("formatted_impact", "")
                    rec_text = f"<b>[{prio}] {title}</b><br/><i>Action:</i> {action}<br/><i>Impact:</i> {impact}"
                    elements.append(Paragraph(rec_text, body_style))
                    elements.append(Spacer(1, 4))

            elif isinstance(sec.content, str):
                elements.append(Paragraph(sec.content.replace("**", ""), body_style))
                elements.append(Spacer(1, 6))

            elif isinstance(sec.content, dict):
                dict_text = "<br/>".join(f"<b>{k.replace('_', ' ').title()}:</b> {v}" for k, v in list(sec.content.items())[:6] if not isinstance(v, (list, dict)))
                elements.append(Paragraph(dict_text, body_style))
                elements.append(Spacer(1, 6))

        # Disclaimer
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"<i>{report.disclaimer}</i>", subtitle_style))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

report_agent = ReportAgent()
