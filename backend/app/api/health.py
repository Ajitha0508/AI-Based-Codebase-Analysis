"""Health check endpoint."""

from fastapi import APIRouter

from app.core.config import settings
from app.rag.vectorstore import vector_store
from app.schemas.codemind_schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def check_health():
    """Verify backend system status, active LLM provider, and ChromaDB health."""
    chroma_status = "connected"
    try:
        vector_store.get_collection()
    except Exception as e:
        chroma_status = f"error: {e}"

    return HealthResponse(
        status="ok",
        version="1.0.0",
        active_llm_provider=settings.LLM_PROVIDER,
        active_embedding_provider=settings.EMBEDDING_PROVIDER,
        chroma_db_status=chroma_status,
    )
