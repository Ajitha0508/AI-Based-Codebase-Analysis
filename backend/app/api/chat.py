"""RAG Chat endpoint for codebase Q&A."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Repository
from app.db.session import get_db
from app.rag.engine import rag_engine
from app.schemas.codemind_schemas import ChatRequest, ChatResponse, SourceReference

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ask a natural language question about an indexed codebase.
    Returns grounded answers with citations, line numbers, and supporting source files.
    """
    repo_id = request.repository_id.lower()

    # Validate that repository exists and is indexed
    stmt = select(Repository).where(Repository.id == repo_id)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository '{request.repository_id}' is not indexed.")

    if repo.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Repository '{request.repository_id}' indexing status is '{repo.status}'. Must be 'ready'."
        )

    try:
        rag_result = await rag_engine.answer_question(
            repository_id=repo_id,
            query=request.query,
            top_k=request.top_k or 5,
        )

        sources = [
            SourceReference(
                file_path=s.get("file_path", ""),
                start_line=s.get("start_line", 1),
                end_line=s.get("end_line", 1),
                content=s.get("content", ""),
                similarity=s.get("similarity", 0.0),
                symbol_name=s.get("symbol_name", ""),
                language=s.get("language", ""),
            )
            for s in rag_result["sources"]
        ]

        return ChatResponse(
            answer=rag_result["answer"],
            sources=sources,
            supporting_files_summary=rag_result["supporting_files_summary"],
            insufficient_evidence=rag_result["insufficient_evidence"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {e}")
