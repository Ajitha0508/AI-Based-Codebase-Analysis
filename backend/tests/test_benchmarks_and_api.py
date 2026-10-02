"""Unit & integration tests for developer velocity benchmarks and FastAPI endpoints."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.session import init_db
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "active_llm_provider" in data
        assert data["chroma_db_status"] == "connected"


@pytest.mark.asyncio
async def test_settings_endpoint_no_secrets():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/settings")
        assert resp.status_code == 200
        data = resp.json()
        # Verify secret keys are NEVER exposed
        assert "OPENAI_API_KEY" not in data
        assert "GEMINI_API_KEY" not in data
        assert "GROQ_API_KEY" not in data
        assert "is_gemini_configured" in data
        assert "is_openai_configured" in data


@pytest.mark.asyncio
async def test_benchmarks_api_and_metrics():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Fetch preloaded benchmarks
        resp = await ac.get("/api/benchmarks")
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "manual_metrics" in data
        assert "ai_metrics" in data
        assert len(data["records"]) > 0

        # Check that speedup percentage is calculated
        summary = data["summary"]
        assert summary["total_recorded_runs"] > 0
        assert summary["speedup_percentage"] > 0.0

        # 2. Add a new live benchmark run
        new_bench = {
            "task_name": "API Endpoint Performance Benchmark",
            "workflow_type": "AI-Assisted",
            "duration_seconds": 320.0,
            "tests_run": 5,
            "tests_passed": 5,
            "review_findings_count": 0,
            "corrections_required": 0,
            "notes": "Verified endpoint with automated load generation.",
        }
        create_resp = await ac.post("/api/benchmarks", json=new_bench)
        assert create_resp.status_code == 201


@pytest.mark.asyncio
async def test_invalid_github_url_rejection_in_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Invalid host
        resp = await ac.post("/api/repositories/index", json={"url": "https://malicious.com/foo/bar"})
        assert resp.status_code in (400, 422)

        # Non-HTTPS
        resp = await ac.post("/api/repositories/index", json={"url": "http://github.com/foo/bar"})
        assert resp.status_code in (400, 422)
