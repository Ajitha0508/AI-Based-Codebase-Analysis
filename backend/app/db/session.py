"""Database engine, async session factory, and startup initialization."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.models import Base, BenchmarkRecord

engine = create_async_engine(
    settings.SQLITE_DB_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize SQLite database tables and preload realistic sample benchmark data."""
    # Ensure data directory exists
    settings.setup_directories()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Preload sample benchmarks if empty
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(BenchmarkRecord).limit(1))
        existing = result.scalar_one_or_none()
        if not existing:
            samples = [
                # Task 1: Auth & JWT Security Review
                BenchmarkRecord(
                    task_name="Authentication & Token Verification Review",
                    workflow_type="Manual",
                    duration_seconds=2700.0,  # 45 mins
                    tests_run=8,
                    tests_passed=6,
                    review_findings_count=3,
                    corrections_required=4,
                    notes="Manual code review of auth handlers, finding timing attacks and token expiration bugs.",
                    is_sample=True,
                ),
                BenchmarkRecord(
                    task_name="Authentication & Token Verification Review",
                    workflow_type="AI-Assisted",
                    duration_seconds=780.0,   # 13 mins
                    tests_run=12,
                    tests_passed=12,
                    review_findings_count=5,
                    corrections_required=1,
                    notes="CodeMind AI highlighted token validation gaps and generated test fixtures immediately.",
                    is_sample=True,
                ),
                # Task 2: Unit Test Suite for Repository Ingestion
                BenchmarkRecord(
                    task_name="Unit Testing File Traversal & Parser",
                    workflow_type="Manual",
                    duration_seconds=3600.0,  # 60 mins
                    tests_run=10,
                    tests_passed=8,
                    review_findings_count=2,
                    corrections_required=3,
                    notes="Writing manual test cases, mocking file systems, checking edge cases.",
                    is_sample=True,
                ),
                BenchmarkRecord(
                    task_name="Unit Testing File Traversal & Parser",
                    workflow_type="AI-Assisted",
                    duration_seconds=900.0,   # 15 mins
                    tests_run=16,
                    tests_passed=16,
                    review_findings_count=1,
                    corrections_required=0,
                    notes="CodeMind AI generated pytest parameterized boundary tests with AST fixtures.",
                    is_sample=True,
                ),
                # Task 3: API Endpoint Documentation & Refactor
                BenchmarkRecord(
                    task_name="API Architecture & Endpoint Documentation",
                    workflow_type="Manual",
                    duration_seconds=2400.0,  # 40 mins
                    tests_run=0,
                    tests_passed=0,
                    review_findings_count=1,
                    corrections_required=2,
                    notes="Manual inspection of routers and compiling OpenAPI descriptions.",
                    is_sample=True,
                ),
                BenchmarkRecord(
                    task_name="API Architecture & Endpoint Documentation",
                    workflow_type="AI-Assisted",
                    duration_seconds=420.0,   # 7 mins
                    tests_run=0,
                    tests_passed=0,
                    review_findings_count=0,
                    corrections_required=0,
                    notes="CodeMind AI extracted route signatures, parameters, and generated Markdown docs.",
                    is_sample=True,
                ),
            ]
            session.add_all(samples)
            await session.commit()
