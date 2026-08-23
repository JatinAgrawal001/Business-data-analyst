from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from app.core.security import get_current_user, get_supabase_user_token
from app.models.user import User
from app.schemas.report import (
    ExecutiveReport,
    GenerateReportRequest,
    ReportExportResponse
)
from app.services.dataset_service import dataset_service
from app.services.report_service import report_service
from app.agents.report_agent import report_agent
from app.core.logging import get_logger

logger = get_logger("app.api.v1.reports")
router = APIRouter(tags=["Reports"])

@router.get("/reports", response_model=List[ExecutiveReport], summary="List Executive Reports")
async def list_reports(
    projectId: Optional[str] = Query(None, description="Filter by project ID"),
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Lists all executive intelligence reports accessible to the requesting user.
    """
    records = await report_service.list_reports(current_user.id, project_id=projectId, user_jwt=user_jwt)
    return [ExecutiveReport(**r) for r in records]

@router.post("/datasets/{dataset_id}/reports/generate", response_model=ExecutiveReport, status_code=status.HTTP_201_CREATED, summary="Generate Executive Intelligence Report")
async def generate_dataset_report(
    dataset_id: str,
    request: Optional[GenerateReportRequest] = None,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Generates a full multi-section Executive Intelligence Report from raw dataset analytics.
    Combines verified KPIs, visual trajectories, 5-category grounded insights, 6-pillar recommendations, and forecasts.
    """
    # 1. Fetch and verify dataset ownership
    dataset_record = await dataset_service.get_dataset(dataset_id, current_user.id, user_jwt=user_jwt)
    file_bytes, file_name, _ = await dataset_service.download_dataset_bytes(dataset_id, current_user.id, user_jwt=user_jwt)
    from app.analytics.profiler import profiler
    file_type = profiler.validate_file_format(file_name)
    df = profiler.parse_file_to_dataframe(file_bytes, file_type)
    profile = profiler.generate_comprehensive_profile(
        df=df,
        dataset_id=dataset_id,
        project_id=dataset_record.get("project_id") or "proj-general",
        name=dataset_record.get("name") or file_name,
        file_type=file_type
    )

    req = request or GenerateReportRequest(dataset_id=dataset_id)
    req.dataset_id = dataset_id

    # 2. Synthesize report via ReportAgent
    report_obj = report_agent.generate_report(
        df=df,
        profile=profile,
        request=req,
        author=current_user.name
    )

    # 3. Persist report in Supabase
    saved_record = await report_service.create_report(
        user_id=current_user.id,
        payload=report_obj.model_dump(),
        user_jwt=user_jwt
    )

    return report_obj

@router.get("/reports/{report_id}", response_model=ExecutiveReport, summary="Get Executive Report by ID")
async def get_report_by_id(
    report_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Retrieves full content, sections, and metadata of a specific executive report.
    """
    record = await report_service.get_report(report_id, current_user.id, user_jwt=user_jwt)
    return ExecutiveReport(**record)

@router.get("/reports/{report_id}/export", summary="Export Report (PDF, HTML, Markdown, or JSON)")
async def export_report(
    report_id: str,
    format: Literal["pdf", "html", "markdown", "json"] = Query("html", description="Export format"),
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Exports the executive report into downloadable PDF, standalone HTML, GitHub-flavored Markdown, or structured JSON.
    """
    record = await report_service.get_report(report_id, current_user.id, user_jwt=user_jwt)
    report_obj = ExecutiveReport(**record)

    safe_title = report_obj.title.lower().replace(" ", "_")[:40]

    if format == "pdf":
        pdf_bytes = report_agent.export_to_pdf(report_obj)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.pdf"'}
        )
    elif format == "html":
        content = report_agent.export_to_html(report_obj)
        return Response(
            content=content,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.html"'}
        )
    elif format == "markdown":
        content = report_agent.export_to_markdown(report_obj)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.md"'}
        )
    else:
        return ReportExportResponse(
            report_id=report_obj.id,
            title=report_obj.title,
            format="json",
            exported_content=report_obj.model_dump_json(indent=2),
            file_name=f"{safe_title}.json"
        )

@router.delete("/reports/{report_id}", summary="Delete / Archive Report")
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    user_jwt: Optional[str] = Depends(get_supabase_user_token)
):
    """
    Deletes or archives an executive report.
    """
    success = await report_service.delete_report(report_id, current_user.id, user_jwt=user_jwt)
    return {"success": success, "message": f"Report {report_id} deleted successfully"}
