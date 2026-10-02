"""FastAPI Application entry point for CodeMind AI."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import (
    benchmarks,
    chat,
    code_review,
    documentation,
    health,
    repositories,
    test_generation,
)
from app.api import settings as settings_api
from app.core.config import settings
from app.db.session import init_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("codemind.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler: initialize DB on startup."""
    logger.info("Initializing CodeMind AI application and database...")
    await init_db()
    logger.info("CodeMind AI backend is ready.")
    yield
    logger.info("Shutting down CodeMind AI backend.")


app = FastAPI(
    title="CodeMind AI — AI-Powered Codebase Assistant Using RAG",
    description=(
        "Production-grade backend for ingesting GitHub repositories, performing language-aware AST chunking, "
        "indexing source code into ChromaDB, and providing grounded RAG question answering, code review, "
        "unit test generation, documentation generation, and developer velocity benchmarking."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler to avoid stack trace leaks
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please verify logs for details."},
    )


# Register API Routers under /api
app.include_router(health.router, prefix="/api")
app.include_router(repositories.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(code_review.router, prefix="/api")
app.include_router(test_generation.router, prefix="/api")
app.include_router(documentation.router, prefix="/api")
app.include_router(benchmarks.router, prefix="/api")
app.include_router(settings_api.router, prefix="/api")

# Mount built frontend if available
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    if (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API routes or docs
        if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        candidate = frontend_dist / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "name": "CodeMind AI API",
            "version": "1.0.0",
            "docs": "/docs",
            "status": "operational",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
