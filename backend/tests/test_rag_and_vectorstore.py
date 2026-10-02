"""Unit tests for ChromaDB vector store isolation and RAG QA engine."""

import pytest

from app.rag.chunker import CodeChunk
from app.rag.engine import rag_engine
from app.rag.vectorstore import vector_store


@pytest.mark.asyncio
async def test_vector_store_repository_isolation():
    # Insert chunks for Repo A
    chunk_a = CodeChunk(
        chunk_id="repo_a:auth.py:1-10:0",
        repository_id="owner_a__repo_a",
        file_path="src/auth.py",
        language="python",
        content="def authenticate_user(token):\n    return verify_jwt(token)",
        start_line=1,
        end_line=10,
        symbol_name="authenticate_user",
    )
    vector_store.add_chunks("owner_a__repo_a", [chunk_a])

    # Insert chunks for Repo B
    chunk_b = CodeChunk(
        chunk_id="repo_b:database.py:1-10:0",
        repository_id="owner_b__repo_b",
        file_path="src/database.py",
        language="python",
        content="def get_db_connection():\n    return create_pool()",
        start_line=1,
        end_line=10,
        symbol_name="get_db_connection",
    )
    vector_store.add_chunks("owner_b__repo_b", [chunk_b])

    # Query Repo A: should only return chunk from Repo A
    results_a = vector_store.search("owner_a__repo_a", "authenticate token", top_k=5)
    assert len(results_a) > 0
    for r in results_a:
        assert r["metadata"]["repository_id"] == "owner_a__repo_a"
        assert r["file_path"] == "src/auth.py"

    # Query Repo B: should only return chunk from Repo B
    results_b = vector_store.search("owner_b__repo_b", "authenticate token", top_k=5)
    # Repo B does not have auth logic
    for r in results_b:
        assert r["metadata"]["repository_id"] == "owner_b__repo_b"


@pytest.mark.asyncio
async def test_rag_engine_grounded_response():
    res = await rag_engine.answer_question(
        repository_id="owner_a__repo_a",
        query="Where is user authentication implemented?",
    )
    assert "answer" in res
    assert "sources" in res
    assert len(res["sources"]) > 0
    assert res["sources"][0]["file_path"] == "src/auth.py"
    assert "src/auth.py (lines 1-10)" in res["supporting_files_summary"]


@pytest.mark.asyncio
async def test_rag_engine_empty_or_missing_repository():
    res = await rag_engine.answer_question(
        repository_id="non_existent_repo",
        query="Explain the architecture",
    )
    assert res["insufficient_evidence"] is True
    assert "does not contain" in res["answer"].lower()
    assert len(res["sources"]) == 0
