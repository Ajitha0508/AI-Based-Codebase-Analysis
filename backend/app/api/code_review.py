"""Code Review endpoint combining static AST checks and AI review."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import sanitize_relative_path
from app.db.models import RepoFile, Repository
from app.db.session import get_db
from app.schemas.codemind_schemas import CodeReviewRequest, CodeReviewResponse, ReviewFinding
from app.services.review_service import review_service

router = APIRouter(prefix="/code-review", tags=["Code Review"])


@router.post("", response_model=CodeReviewResponse)
async def review_repository_file(
    request: CodeReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Perform security and architectural code review on a selected repository file.
    Combines deterministic static AST rules with LLM suggestions.
    """
    repo_id = request.repository_id.lower()

    # Validate repository
    stmt = select(Repository).where(Repository.id == repo_id)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository '{request.repository_id}' not found.")

    code_to_review = ""
    language = "python"

    if request.code_override:
        code_to_review = request.code_override
        safe_path = request.file_path or "snippet.py"
    else:
        try:
            safe_path = sanitize_relative_path(request.file_path)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        file_stmt = select(RepoFile).where(RepoFile.repository_id == repo_id, RepoFile.path == safe_path)
        file_res = await db.execute(file_stmt)
        file_rec = file_res.scalar_one_or_none()
        if not file_rec:
            raise HTTPException(status_code=404, detail=f"File '{request.file_path}' not found in repository.")

        language = file_rec.language
        disk_path = settings.DATA_DIR / "repos" / repo_id / safe_path
        if not disk_path.exists():
            raise HTTPException(status_code=404, detail="File content not found on disk.")

        try:
            code_to_review = disk_path.read_text(encoding="utf-8")
        except Exception:
            code_to_review = disk_path.read_text(encoding="latin-1")

    review_result = await review_service.review_code(
        code=code_to_review,
        file_path=request.file_path,
        language=language,
    )

    findings = [
        ReviewFinding(
            title=f["title"],
            severity=f["severity"],
            category=f["category"],
            file_path=f["file_path"],
            line_range=f["line_range"],
            explanation=f["explanation"],
            why_it_matters=f["why_it_matters"],
            suggested_fix=f["suggested_fix"],
            verification_status=f["verification_status"],
            human_review_required=f["human_review_required"],
        )
        for f in review_result["findings"]
    ]

    return CodeReviewResponse(
        file_path=review_result["file_path"],
        language=review_result["language"],
        total_findings=review_result["total_findings"],
        severity_counts=review_result["severity_counts"],
        findings=findings,
        human_review_notice=review_result["human_review_notice"],
    )
