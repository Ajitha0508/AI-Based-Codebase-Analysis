"""Unit-Test Generation endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import sanitize_relative_path
from app.db.models import RepoFile, Repository
from app.db.session import get_db
from app.schemas.codemind_schemas import TestGenRequest, TestGenResponse
from app.services.test_service import test_service

router = APIRouter(prefix="/test-generation", tags=["Unit Tests"])


@router.post("", response_model=TestGenResponse)
async def generate_unit_tests(
    request: TestGenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate comprehensive unit tests (pytest for Python, Jest for JS/TS)
    for a selected repository file or specific function/class symbol.
    """
    repo_id = request.repository_id.lower()

    # Validate repository
    stmt = select(Repository).where(Repository.id == repo_id)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository '{request.repository_id}' not found.")

    try:
        safe_path = sanitize_relative_path(request.file_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    file_stmt = select(RepoFile).where(RepoFile.repository_id == repo_id, RepoFile.path == safe_path)
    file_res = await db.execute(file_stmt)
    file_rec = file_res.scalar_one_or_none()
    if not file_rec:
        raise HTTPException(status_code=404, detail=f"File '{request.file_path}' not found in repository.")

    disk_path = settings.DATA_DIR / "repos" / repo_id / safe_path
    if not disk_path.exists():
        raise HTTPException(status_code=404, detail="File content not found on disk.")

    try:
        code_content = disk_path.read_text(encoding="utf-8")
    except Exception:
        code_content = disk_path.read_text(encoding="latin-1")

    res = await test_service.generate_tests(
        code=code_content,
        file_path=request.file_path,
        target_symbol=request.symbol_name,
        language=file_rec.language,
    )

    return TestGenResponse(
        file_path=res["file_path"],
        language=res["language"],
        framework=res["framework"],
        target_symbol=res["target_symbol"],
        generated_test_code=res["generated_test_code"],
        discovered_symbols=res["discovered_symbols"],
        assumptions=res["assumptions"],
        execution_note=res["execution_note"],
    )
