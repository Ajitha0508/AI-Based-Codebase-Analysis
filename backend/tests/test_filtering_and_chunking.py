"""Unit tests for file filtering, binary detection, secret exclusion, and language-aware chunking."""

from app.rag.chunker import chunk_code_file
from app.repository.filter import (
    get_file_language,
    is_binary_content,
    is_eligible_source_file,
    is_sensitive_file,
)


def test_eligible_source_files():
    eligible, _ = is_eligible_source_file("app/main.py", 1024)
    assert eligible is True

    eligible, _ = is_eligible_source_file("frontend/src/App.jsx", 2048)
    assert eligible is True

    eligible, _ = is_eligible_source_file("models/User.java", 4096)
    assert eligible is True


def test_ignored_directories_and_secrets():
    # Ignored directories
    eligible, reason = is_eligible_source_file("node_modules/react/index.js")
    assert eligible is False
    assert "node_modules" in reason

    eligible, reason = is_eligible_source_file(".venv/lib/site-packages/pkg.py")
    assert eligible is False
    assert ".venv" in reason

    # Sensitive files
    assert is_sensitive_file(".env") is True
    assert is_sensitive_file(".env.production") is True
    assert is_sensitive_file("id_rsa") is True
    assert is_sensitive_file("server.key") is True
    assert is_sensitive_file("cert.pem") is True
    assert is_sensitive_file("credentials.json") is True

    eligible, reason = is_eligible_source_file(".env")
    assert eligible is False


def test_binary_exclusion():
    eligible, reason = is_eligible_source_file("assets/image.png")
    assert eligible is False
    assert "Binary" in reason

    eligible, reason = is_eligible_source_file("archive.zip")
    assert eligible is False

    # Binary content null-byte check
    assert is_binary_content(b"Hello\x00World") is True
    assert is_binary_content(b"print('Hello, World!')\n") is False


def test_language_detection():
    assert get_file_language("main.py") == "python"
    assert get_file_language("index.ts") == "typescript"
    assert get_file_language("App.tsx") == "typescript"
    assert get_file_language("schema.sql") == "sql"
    assert get_file_language("Dockerfile") == "dockerfile"


def test_code_chunking_preserves_metadata():
    code_content = (
        "def add(a, b):\n"
        "    \"\"\"Add two numbers.\"\"\"\n"
        "    return a + b\n\n"
        "class Calculator:\n"
        "    def multiply(self, x, y):\n"
        "        return x * y\n"
    )
    chunks = chunk_code_file(
        content=code_content,
        file_path="math_utils.py",
        repository_id="test__repo",
        language="python",
        chunk_size_chars=100,
    )
    assert len(chunks) >= 1
    chunk = chunks[0]
    assert chunk.repository_id == "test__repo"
    assert chunk.file_path == "math_utils.py"
    assert chunk.language == "python"
    assert chunk.start_line >= 1
    assert chunk.end_line >= chunk.start_line
    assert len(chunk.content) > 0
