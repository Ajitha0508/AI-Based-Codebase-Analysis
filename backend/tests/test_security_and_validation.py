"""Unit tests for GitHub URL validation, SSRF protection, path traversal defenses, and secret redaction."""

import pytest

from app.core.security import (
    redact_secrets,
    sanitize_relative_path,
    validate_github_url,
)


def test_valid_github_urls():
    url, owner, repo = validate_github_url("https://github.com/pallets/flask")
    assert url == "https://github.com/pallets/flask"
    assert owner == "pallets"
    assert repo == "flask"

    url, owner, repo = validate_github_url("https://github.com/tiangolo/fastapi.git")
    assert url == "https://github.com/tiangolo/fastapi"
    assert owner == "tiangolo"
    assert repo == "fastapi"


def test_invalid_github_urls_rejected():
    # Non-HTTPS
    with pytest.raises(ValueError, match="Only secure HTTPS URLs are permitted"):
        validate_github_url("http://github.com/pallets/flask")

    # Non-GitHub host
    with pytest.raises(ValueError, match="Only 'github.com' is supported"):
        validate_github_url("https://gitlab.com/pallets/flask")

    # Localhost / SSRF
    with pytest.raises(ValueError, match="Only 'github.com' is supported"):
        validate_github_url("https://localhost:8000/test/repo")

    # Malicious cloud metadata
    with pytest.raises(ValueError, match="Only 'github.com' is supported"):
        validate_github_url("https://169.254.169.254/latest/meta-data")

    # Empty URL
    with pytest.raises(ValueError, match="Repository URL must be a non-empty string"):
        validate_github_url("")

    # Traversal in owner or repo name
    with pytest.raises(ValueError):
        validate_github_url("https://github.com/../evil")


def test_path_traversal_sanitization():
    # Valid paths
    assert sanitize_relative_path("src/core/config.py") == "src/core/config.py"
    assert sanitize_relative_path("app\\main.py") == "app/main.py"
    assert sanitize_relative_path("/components/Button.jsx") == "components/Button.jsx"

    # Traversal attempts
    with pytest.raises(ValueError, match="Path traversal detected"):
        sanitize_relative_path("../../etc/passwd")

    with pytest.raises(ValueError, match="Path traversal detected"):
        sanitize_relative_path("src/../../windows/system32/cmd.exe")

    with pytest.raises(ValueError, match="Empty or invalid"):
        sanitize_relative_path("/")


def test_secret_redaction():
    text = "Authorization token: ghp_123456789012345678901234567890123456 in header"
    redacted = redact_secrets(text)
    assert "[REDACTED_SECRET]" in redacted
    assert "ghp_123456789012345678901234567890123456" not in redacted

    text2 = "API key configured as api_key = 'sk-1234567890abcdefghijklmnopqrstuvwxyz'"
    redacted2 = redact_secrets(text2)
    assert "[REDACTED_SECRET]" in redacted2
