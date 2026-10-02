"""Application configuration and settings."""

from pathlib import Path
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Central configuration for CodeMind AI."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    CODEMIND_ENV: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Storage paths
    DATA_DIR: Path = BASE_DIR / "data"
    SQLITE_DB_URL: str = "sqlite+aiosqlite:///./data/codemind.db"
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "chroma_db")

    # LLM Provider: local, gemini, openai, groq, ollama
    LLM_PROVIDER: str = "local"
    LLM_MODEL: str = "default"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Embedding Provider: local, gemini, openai
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Ingestion & Chunking parameters
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    RETRIEVAL_TOP_K: int = 5
    MAX_FILE_SIZE_KB: int = 500
    MAX_REPO_FILES: int = 500

    # GitHub integration
    GITHUB_TOKEN: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    def setup_directories(self) -> None:
        """Ensure required data directories exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        Path(self.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.setup_directories()
