"""Settings inspection endpoint (safe without exposing secrets)."""

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.codemind_schemas import SettingsStatusResponse

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsStatusResponse)
async def get_settings_status():
    """Retrieve operational configuration without exposing secret keys."""
    return SettingsStatusResponse(
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.LLM_MODEL,
        is_gemini_configured=bool(settings.GEMINI_API_KEY),
        is_openai_configured=bool(settings.OPENAI_API_KEY),
        is_groq_configured=bool(settings.GROQ_API_KEY),
        embedding_provider=settings.EMBEDDING_PROVIDER,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        retrieval_top_k=settings.RETRIEVAL_TOP_K,
        max_file_size_kb=settings.MAX_FILE_SIZE_KB,
    )
