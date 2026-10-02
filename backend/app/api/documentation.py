"""Documentation generation endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import RepoFile, Repository
from app.db.session import get_db
from app.schemas.codemind_schemas import DocGenRequest, DocGenResponse
from app.services.doc_service import doc_service

router = APIRouter(prefix="/documentation", tags=["Documentation"])


@router.post("", response_model=DocGenResponse)
async def generate_documentation(
    request: DocGenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate structured, grounded Markdown documentation for an indexed repository.
    Doc types: 'overview', 'module', 'api', 'setup', 'readme'.
    """
    repo_id = request.repository_id.lower()

    # Validate repository
    stmt = select(Repository).where(Repository.id == repo_id)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository '{request.repository_id}' not found.")

    # Get sample of repository files
    f_stmt = select(RepoFile).where(RepoFile.repository_id == repo_id).limit(25)
    f_res = await db.execute(f_stmt)
    files = f_res.scalars().all()

    context_files = []
    for f in files:
        disk_path = settings.DATA_DIR / "repos" / repo_id / f.path
        content = ""
        if disk_path.exists():
            try:
                content = disk_path.read_text(encoding="utf-8")[:2000]
            except Exception:
                pass
        context_files.append({
            "path": f.path,
            "language": f.language,
            "line_count": f.line_count,
            "content": content,
        })

    doc_res = await doc_service.generate_doc(
        doc_type=request.doc_type,
        context_files=context_files,
        repo_name=f"{repo.owner}/{repo.name}",
    )

    return DocGenResponse(
        doc_type=doc_res["doc_type"],
        repo_name=doc_res["repo_name"],
        markdown_content=doc_res["markdown_content"],
    )
