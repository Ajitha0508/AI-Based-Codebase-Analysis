"""File filtering, binary detection, extension-to-language mapping, and secret exclusion."""

import re
from pathlib import Path
from typing import Optional, Set, Tuple

# Blocked directory names anywhere in path
IGNORED_DIRECTORIES: Set[str] = {
    ".git",
    ".github",
    ".gitlab",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "vendor",
    ".terraform",
    ".next",
    ".nuxt",
    ".turbo",
    "target",
    "bin",
    "obj",
    "coverage",
    ".coverage",
    "htmlcov",
    "eggs",
    ".eggs",
}

# Explicitly sensitive file patterns to exclude
SENSITIVE_FILENAME_PATTERNS = [
    re.compile(r"^\.env(\..+)?$", re.IGNORECASE),
    re.compile(r".*\.pem$", re.IGNORECASE),
    re.compile(r".*\.key$", re.IGNORECASE),
    re.compile(r"^id_rsa.*$", re.IGNORECASE),
    re.compile(r"^id_ed25519.*$", re.IGNORECASE),
    re.compile(r".*credentials.*\.json$", re.IGNORECASE),
    re.compile(r".*service[-_]?account.*\.json$", re.IGNORECASE),
    re.compile(r".*\.p12$", re.IGNORECASE),
    re.compile(r".*\.pfx$", re.IGNORECASE),
    re.compile(r".*\.kdbx$", re.IGNORECASE),
]

# Supported source file extensions and their normalized language identifiers
LANGUAGE_MAP = {
    ".py": "python",
    ".pyw": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c_header",
    ".hpp": "cpp_header",
    ".cs": "csharp",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sql": "sql",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".markdown": "markdown",
    ".rst": "rst",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".bat": "batch",
    ".ps1": "powershell",
    ".dockerfile": "dockerfile",
    "Dockerfile": "dockerfile",
}

# Binary file extensions that should never be processed as text
BINARY_EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".bmp", ".tiff",
    ".mp3", ".wav", ".ogg", ".mp4", ".mov", ".avi", ".mkv",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".o", ".a", ".lib",
    ".class", ".pyc", ".pyo", ".pyd", ".jar", ".war", ".wasm",
    ".db", ".sqlite", ".sqlite3", ".parquet", ".arrow",
    ".ttf", ".woff", ".woff2", ".eot",
}


def is_sensitive_file(filename: str) -> bool:
    """Check if the filename matches common secret or credential patterns."""
    for pattern in SENSITIVE_FILENAME_PATTERNS:
        if pattern.match(filename):
            return True
    return False


def get_file_language(file_path: str) -> Optional[str]:
    """Detect language from file path extension or special filename."""
    path = Path(file_path)
    name = path.name
    if name == "Dockerfile" or name.startswith("Dockerfile."):
        return "dockerfile"
    ext = path.suffix.lower()
    return LANGUAGE_MAP.get(ext)


def is_eligible_source_file(file_path: str, file_size_bytes: int = 0, max_size_kb: int = 500) -> Tuple[bool, str]:
    """
    Determine if a file is eligible for indexing.
    Returns:
        (is_eligible, reason)
    """
    normalized_path = file_path.replace("\\", "/")
    parts = normalized_path.split("/")
    filename = parts[-1]

    # Check ignored directories
    for part in parts[:-1]:
        if part in IGNORED_DIRECTORIES or part.startswith("."):
            return False, f"Directory '{part}' is ignored"

    # Check sensitive files
    if is_sensitive_file(filename):
        return False, "File is flagged as potentially sensitive or secret"

    # Check binary extensions
    ext = Path(filename).suffix.lower()
    if ext in BINARY_EXTENSIONS:
        return False, f"Binary file extension '{ext}' is excluded"

    # Check size limit
    if file_size_bytes > max_size_kb * 1024:
        return False, f"File exceeds maximum allowed size ({max_size_kb} KB)"

    # Check if supported source language
    lang = get_file_language(filename)
    if not lang:
        return False, "File extension is not in supported source languages"

    return True, "Eligible"


def is_binary_content(content: bytes) -> bool:
    """Check if content bytes contain null bytes or high ratio of non-text characters."""
    if not content:
        return False
    if b"\x00" in content:
        return True
    # Sample first 1024 bytes
    sample = content[:1024]
    text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
    non_text = sample.translate(None, text_chars)
    return len(non_text) / len(sample) > 0.30
