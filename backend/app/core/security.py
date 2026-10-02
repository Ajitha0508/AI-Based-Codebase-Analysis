"""Security utilities: SSRF defense, URL validation, path sanitization, and secret redaction."""

import ipaddress
import re
import socket
from typing import Tuple
from urllib.parse import urlparse

GITHUB_REPO_REGEX = re.compile(
    r"^https://github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+?)(?:\.git)?/?$"
)

# Common sensitive patterns to redact
SECRET_PATTERNS = [
    re.compile(r"(api[_-]?key|secret|token|password|auth|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?", re.IGNORECASE),
    re.compile(r"ghp_[0-9a-zA-Z]{36}"),
    re.compile(r"github_pat_[0-9a-zA-Z_]{82}"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),
]

# Reserved/private IP networks for SSRF defense
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local & cloud metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def validate_github_url(url: str) -> Tuple[str, str, str]:
    """
    Validate that a given URL is a legitimate public GitHub repository URL.
    Returns:
        tuple (normalized_url, owner, repo)
    Raises:
        ValueError if URL is invalid, malicious, or non-GitHub.
    """
    if not url or not isinstance(url, str):
        raise ValueError("Repository URL must be a non-empty string.")

    url = url.strip()
    parsed = urlparse(url)

    # Must be HTTPS
    if parsed.scheme.lower() != "https":
        raise ValueError("Only secure HTTPS URLs are permitted.")

    # Hostname must strictly be github.com
    hostname = (parsed.hostname or "").lower()
    if hostname != "github.com":
        raise ValueError(f"Disallowed host '{hostname}'. Only 'github.com' is supported.")

    # Check SSRF / host resolution
    try:
        resolved_ips = socket.gethostbyname_ex(hostname)[2]
        for ip_str in resolved_ips:
            ip_obj = ipaddress.ip_address(ip_str)
            for network in BLOCKED_NETWORKS:
                if ip_obj in network:
                    raise ValueError(f"Host '{hostname}' resolved to blocked private/local IP address.")
    except socket.gaierror:
        # If offline or DNS fails, regex validation will still ensure strict domain syntax
        pass

    match = GITHUB_REPO_REGEX.match(url)
    if not match:
        raise ValueError("Invalid GitHub repository URL format. Expected: https://github.com/owner/repository")

    owner, repo = match.groups()
    if owner in ("..", ".", "") or repo in ("..", ".", ""):
        raise ValueError("Invalid owner or repository name.")

    # Normalize URL
    normalized_url = f"https://github.com/{owner}/{repo}"
    return normalized_url, owner, repo


def sanitize_relative_path(path_str: str) -> str:
    """
    Sanitize and validate a relative file path to prevent directory traversal.
    """
    cleaned = path_str.replace("\\", "/").strip()
    if cleaned.startswith("/"):
        cleaned = cleaned.lstrip("/")

    parts = cleaned.split("/")
    safe_parts = []
    for part in parts:
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError(f"Path traversal detected in path '{path_str}'.")
        safe_parts.append(part)

    safe_path = "/".join(safe_parts)
    if not safe_path:
        raise ValueError("Empty or invalid relative file path.")

    return safe_path


def redact_secrets(text: str) -> str:
    """Redact sensitive API keys, passwords, and tokens from strings/logs."""
    if not text:
        return text
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted
