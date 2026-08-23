import io
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from app.analytics.profiler import profiler
from app.agents.report_agent import report_agent
from app.schemas.report import GenerateReportRequest, ExecutiveReport

def test_report_agent_full_synthesis_and_sections():
    """
    Unit test for ReportAgent multi-pillar executive intelligence synthesis with all 10 mandatory sections.
    """
    np.random.seed(505)
    dates = pd.date_range(start="2025-01-01", periods=20, freq="W").strftime("%Y-%m-%d").tolist()
    tiers = ["Enterprise", "Mid-Market", "SMB", "Startup"] * 5
    revenue = [10000 + i * 800 + int(np.random.randint(-200, 200)) for i in range(20)]
    units = [50 + i * 4 for i in range(20)]

    df = pd.DataFrame({
        "order_date": dates,
        "customer_tier": tiers,
        "revenue_usd": revenue,
        "units_sold": units
    })

    profile = profiler.generate_comprehensive_profile(
        df=df,
        dataset_id="ds-report-test-01",
        project_id="proj-rep",
        name="Executive Revenue Telemetry",
        file_type="csv"
    )

    req = GenerateReportRequest(
        dataset_id="ds-report-test-01",
        title="Q1 Executive Revenue Telemetry Brief",
        subtitle="Operational and predictive revenue assessment",
        include_kpis=True,
        include_charts=True,
        include_insights=True,
        include_recommendations=True,
        include_forecast=True
    )

    report = report_agent.generate_report(df, profile, req, author="Dr. Sarah Jenkins")

    assert isinstance(report, ExecutiveReport)
    assert report.title == "Q1 Executive Revenue Telemetry Brief"
    assert report.author == "Dr. Sarah Jenkins"
    assert report.dataset_id == "ds-report-test-01"
    assert len(report.key_takeaways) >= 3
    assert len(report.sections) == 10

    section_types = [s.type for s in report.sections]
    # Check all 10 mandatory sections
    assert "executive_summary" in section_types
    assert "dataset_overview" in section_types
    assert "data_quality" in section_types
    assert "kpi_grid" in section_types
    assert "chart_view" in section_types
    assert "key_insights" in section_types
    assert "risks_list" in section_types
    assert "recommendations_table" in section_types
    assert "forecast_view" in section_types
    assert "limitations_view" in section_types

    # Test Markdown export
    md_content = report_agent.export_to_markdown(report)
    assert "# Q1 Executive Revenue Telemetry Brief" in md_content
    assert "Executive Summary" in md_content
    assert "Dataset Overview" in md_content
    assert "Data Quality" in md_content
    assert "Key Performance Indicators" in md_content
    assert "Limitations" in md_content

    # Test HTML export
    html_content = report_agent.export_to_html(report)
    assert "<!DOCTYPE html>" in html_content
    assert "Q1 Executive Revenue Telemetry Brief" in html_content
    assert "Dr. Sarah Jenkins" in html_content
    assert "Print / Save PDF" in html_content

    # Test PDF binary export
    pdf_bytes = report_agent.export_to_pdf(report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")

def test_report_api_endpoints_full_lifecycle(client: TestClient):
    """
    Integration test exercising full REST API lifecycle for report generation, retrieval, PDF/HTML/Markdown export, and deletion.
    """
    csv_payload = (
        "date,region,revenue,expenses,profit\n"
        "2026-01-01,North,10000,6000,4000\n"
        "2026-01-02,South,12000,7000,5000\n"
        "2026-01-03,East,15000,8000,7000\n"
        "2026-01-04,West,11000,6500,4500\n"
        "2026-01-05,North,13000,7200,5800\n"
        "2026-01-06,South,14000,7500,6500\n"
        "2026-01-07,East,17000,8500,8500\n"
        "2026-01-08,West,12500,7000,5500\n"
    )

    # 1. Upload dataset
    upload_res = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("regional_financials.csv", io.BytesIO(csv_payload.encode("utf-8")), "text/csv")},
        data={"projectId": "proj-financials", "customName": "Regional Financials 2026"}
    )
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["id"]

    # 2. POST /api/v1/datasets/{id}/reports/generate
    gen_res = client.post(
        f"/api/v1/datasets/{dataset_id}/reports/generate",
        json={
            "dataset_id": dataset_id,
            "title": "2026 Regional Financial Performance Report",
            "subtitle": "Synthesized commercial revenue audit"
        }
    )
    assert gen_res.status_code == 201
    report_data = gen_res.json()
    assert report_data["title"] == "2026 Regional Financial Performance Report"
    report_id = report_data["id"]
    assert len(report_data["sections"]) == 10

    # 3. GET /api/v1/reports
    list_res = client.get("/api/v1/reports")
    assert list_res.status_code == 200
    assert any(r["id"] == report_id for r in list_res.json())

    # 4. GET /api/v1/reports/{report_id}
    get_res = client.get(f"/api/v1/reports/{report_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == report_id

    # 5. GET /api/v1/reports/{report_id}/export?format=pdf (PDF binary download)
    export_pdf = client.get(f"/api/v1/reports/{report_id}/export?format=pdf")
    assert export_pdf.status_code == 200
    assert export_pdf.headers["content-type"] == "application/pdf"
    assert export_pdf.content.startswith(b"%PDF")

    # 6. GET /api/v1/reports/{report_id}/export?format=html (HTML download)
    export_html = client.get(f"/api/v1/reports/{report_id}/export?format=html")
    assert export_html.status_code == 200
    assert "text/html" in export_html.headers["content-type"]
    assert "<!DOCTYPE html>" in export_html.text

    # 7. GET /api/v1/reports/{report_id}/export?format=markdown
    export_md = client.get(f"/api/v1/reports/{report_id}/export?format=markdown")
    assert export_md.status_code == 200
    assert "2026 Regional Financial Performance Report" in export_md.text

    # 8. DELETE /api/v1/reports/{report_id}
    del_res = client.delete(f"/api/v1/reports/{report_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True
