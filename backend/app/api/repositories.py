"""Repository management, indexing, file explorer, and deletion endpoints."""

import json
import shutil
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import sanitize_relative_path
from app.db.models import RepoFile, Repository
from app.db.session import get_db
from app.rag.vectorstore import vector_store
from app.repository.ingestion import IngestionError, ingestion_service
from app.schemas.codemind_schemas import (
    FileContentResponse,
    IndexRepoRequest,
    RepoFileResponse,
    RepositoryResponse,
)

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.post("/index", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def index_repository(
    request: IndexRepoRequest,
    db: AsyncSession = Depends(get_db),
):
    """Index a public GitHub repository."""
    try:
        repo = await ingestion_service.ingest_repository(
            repo_url=request.url,
            db=db,
            force_refresh=request.force_refresh,
        )
        return RepositoryResponse(
            id=repo.id,
            url=repo.url,
            owner=repo.owner,
            name=repo.name,
            default_branch=repo.default_branch,
            commit_sha=repo.commit_sha,
            description=repo.description,
            primary_language=repo.primary_language,
            file_count=repo.file_count,
            chunk_count=repo.chunk_count,
            status=repo.status,
            error_message=repo.error_message,
            created_at=repo.created_at,
            updated_at=repo.updated_at,
        )
    except IngestionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected indexing error: {e}")


@router.get("", response_model=List[RepositoryResponse])
async def list_repositories(db: AsyncSession = Depends(get_db)):
    """List all indexed repositories."""
    stmt = select(Repository).order_by(Repository.updated_at.desc())
    res = await db.execute(stmt)
    repos = res.scalars().all()
    return [
        RepositoryResponse(
            id=r.id,
            url=r.url,
            owner=r.owner,
            name=r.name,
            default_branch=r.default_branch,
            commit_sha=r.commit_sha,
            description=r.description,
            primary_language=r.primary_language,
            file_count=r.file_count,
            chunk_count=r.chunk_count,
            status=r.status,
            error_message=r.error_message,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in repos
    ]


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(repository_id: str, db: AsyncSession = Depends(get_db)):
    """Get metadata for a specific repository."""
    stmt = select(Repository).where(Repository.id == repository_id.lower())
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository '{repository_id}' not found.")

    return RepositoryResponse(
        id=repo.id,
        url=repo.url,
        owner=repo.owner,
        name=repo.name,
        default_branch=repo.default_branch,
        commit_sha=repo.commit_sha,
        description=repo.description,
        primary_language=repo.primary_language,
        file_count=repo.file_count,
        chunk_count=repo.chunk_count,
        status=repo.status,
        error_message=repo.error_message,
        created_at=repo.created_at,
        updated_at=repo.updated_at,
    )


@router.post("/{repository_id}/refresh", response_model=RepositoryResponse)
async def refresh_repository(repository_id: str, db: AsyncSession = Depends(get_db)):
    """Refresh index for an existing repository."""
    stmt = select(Repository).where(Repository.id == repository_id.lower())
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository '{repository_id}' not found.")

    try:
        refreshed = await ingestion_service.ingest_repository(
            repo_url=repo.url,
            db=db,
            force_refresh=True,
        )
        return RepositoryResponse(
            id=refreshed.id,
            url=refreshed.url,
            owner=refreshed.owner,
            name=refreshed.name,
            default_branch=refreshed.default_branch,
            commit_sha=refreshed.commit_sha,
            description=refreshed.description,
            primary_language=refreshed.primary_language,
            file_count=refreshed.file_count,
            chunk_count=refreshed.chunk_count,
            status=refreshed.status,
            error_message=refreshed.error_message,
            created_at=refreshed.created_at,
            updated_at=refreshed.updated_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {e}")


@router.delete("/{repository_id}/index", status_code=status.HTTP_200_OK)
async def delete_repository_index(repository_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a repository's vector index, file records, and cached files."""
    repo_id = repository_id.lower()
    stmt = select(Repository).where(Repository.id == repo_id)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository '{repository_id}' not found.")

    # 1. Delete Chroma vectors
    vector_store.delete_repository_index(repo_id)

    # 2. Delete cached files on disk
    local_dir = settings.DATA_DIR / "repos" / repo_id
    if local_dir.exists():
        shutil.rmtree(local_dir, ignore_errors=True)

    # 3. Delete from database
    await db.execute(delete(RepoFile).where(RepoFile.repository_id == repo_id))
    await db.execute(delete(Repository).where(Repository.id == repo_id))
    await db.commit()

    return {"message": f"Successfully deleted index and records for repository '{repository_id}'."}


@router.get("/{repository_id}/files", response_model=List[RepoFileResponse])
async def list_repository_files(
    repository_id: str,
    language: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List indexed files for a repository."""
    stmt = select(RepoFile).where(RepoFile.repository_id == repository_id.lower())
    if language:
        stmt = stmt.where(RepoFile.language == language.lower())

    res = await db.execute(stmt)
    files = res.scalars().all()

    output = []
    for f in files:
        symbols = None
        if f.ast_symbols_json:
            try:
                symbols = json.loads(f.ast_symbols_json)
            except Exception:
                pass
        output.append(
            RepoFileResponse(
                id=f.id,
                repository_id=f.repository_id,
                path=f.path,
                language=f.language,
                size_bytes=f.size_bytes,
                line_count=f.line_count,
                ast_symbols=symbols,
            )
        )
    return output


@router.get("/{repository_id}/files/content", response_model=FileContentResponse)
async def get_file_content(
    repository_id: str,
    path: str = Query(..., description="Relative file path"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full content of a specific indexed file."""
    repo_id = repository_id.lower()
    try:
        safe_path = sanitize_relative_path(path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Check file record in DB
    stmt = select(RepoFile).where(
        RepoFile.repository_id == repo_id,
        RepoFile.path == safe_path,
    )
    res = await db.execute(stmt)
    file_record = res.scalar_one_or_none()
    if not file_record:
        raise HTTPException(status_code=404, detail=f"File '{path}' not found in repository '{repository_id}'.")

    # Read from local disk cache
    cached_path = settings.DATA_DIR / "repos" / repo_id / safe_path
    if not cached_path.exists():
        raise HTTPException(status_code=404, detail=f"File content not available on disk for '{path}'.")

    try:
        content = cached_path.read_text(encoding="utf-8")
    except Exception:
        content = cached_path.read_text(encoding="latin-1")

    symbols = None
    if file_record.ast_symbols_json:
        try:
            symbols = json.loads(file_record.ast_symbols_json)
        except Exception:
            pass

    return FileContentResponse(
        repository_id=repo_id,
        file_path=file_record.path,
        language=file_record.language,
        line_count=file_record.line_count,
        content=content,
        ast_symbols=symbols,
    )
