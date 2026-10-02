"""GitHub repository ingestion module supporting REST API, tree traversal, and streaming zip archives."""

import io
import json
import logging
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import sanitize_relative_path, validate_github_url
from app.db.models import RepoFile, Repository
from app.rag.chunker import chunk_code_file
from app.rag.vectorstore import vector_store
from app.repository.filter import get_file_language, is_binary_content, is_eligible_source_file
from app.repository.parser import parse_generic_symbols, parse_python_ast

logger = logging.getLogger("codemind.ingestion")


class IngestionError(Exception):
    pass


class RepositoryIngestionService:
    """Handles validating, fetching, scanning, and indexing GitHub repositories."""

    def __init__(self):
        self.vector_store = vector_store

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeMind-AI-Assistant",
        }
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
        return headers

    async def fetch_repo_metadata(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository details from the GitHub REST API."""
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(api_url, headers=headers)
            except httpx.RequestError as e:
                raise IngestionError(f"Network error communicating with GitHub: {e}")

            if resp.status_code == 404:
                raise IngestionError(f"GitHub repository '{owner}/{repo}' not found or is private.")
            elif resp.status_code == 403 and "rate limit" in resp.text.lower():
                raise IngestionError("GitHub API rate limit exceeded. Set GITHUB_TOKEN in settings to increase limits.")
            elif resp.status_code != 200:
                raise IngestionError(f"GitHub API returned error ({resp.status_code}): {resp.text}")

            repo_data = resp.json()
            default_branch = repo_data.get("default_branch", "main")

            # Fetch latest commit SHA
            commit_sha = ""
            commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{default_branch}"
            try:
                c_resp = await client.get(commits_url, headers=headers)
                if c_resp.status_code == 200:
                    commit_sha = c_resp.json().get("sha", "")
            except Exception:
                commit_sha = "latest"

            return {
                "owner": owner,
                "name": repo,
                "default_branch": default_branch,
                "commit_sha": commit_sha or "latest",
                "description": repo_data.get("description", ""),
                "primary_language": repo_data.get("language", "Unknown"),
            }

    async def ingest_repository(
        self,
        repo_url: str,
        db: AsyncSession,
        force_refresh: bool = False,
    ) -> Repository:
        """
        Validate, download, process files, extract AST, chunk, and index into ChromaDB & SQLite.
        """
        normalized_url, owner, repo_name = validate_github_url(repo_url)
        repo_id = f"{owner}__{repo_name}".lower()

        # Check existing database entry
        stmt = select(Repository).where(Repository.id == repo_id)
        result = await db.execute(stmt)
        repo_record = result.scalar_one_or_none()

        # Fetch metadata
        meta = await self.fetch_repo_metadata(owner, repo_name)
        commit_sha = meta["commit_sha"]

        # Prevent duplicate indexing if commit SHA is identical
        if repo_record and repo_record.status == "ready" and repo_record.commit_sha == commit_sha and not force_refresh:
            return repo_record

        # Create or update record in pending state
        if not repo_record:
            repo_record = Repository(
                id=repo_id,
                url=normalized_url,
                owner=owner,
                name=repo_name,
                default_branch=meta["default_branch"],
                commit_sha=commit_sha,
                description=meta["description"],
                primary_language=meta["primary_language"],
                status="indexing",
            )
            db.add(repo_record)
        else:
            repo_record.status = "indexing"
            repo_record.commit_sha = commit_sha
            repo_record.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(repo_record)

        try:
            # Download zip archive stream
            archive_url = f"https://github.com/{owner}/{repo_name}/archive/{commit_sha}.zip"
            headers = self._get_headers()

            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                resp = await client.get(archive_url, headers=headers)
                if resp.status_code != 200:
                    # Fallback to default branch zip
                    archive_url = f"https://github.com/{owner}/{repo_name}/archive/refs/heads/{meta['default_branch']}.zip"
                    resp = await client.get(archive_url, headers=headers)

                if resp.status_code != 200:
                    raise IngestionError(f"Could not download repository archive from GitHub ({resp.status_code})")

                archive_bytes = resp.content

            # Process zip content in-memory
            with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
                # Remove stale files from DB & Chroma
                await db.execute(delete(RepoFile).where(RepoFile.repository_id == repo_id))
                self.vector_store.delete_repository_index(repo_id)

                file_records = []
                all_chunks = []
                scanned_count = 0

                # GitHub zips have a root directory like `repo-sha/...`
                namelist = z.namelist()
                root_prefix = namelist[0].split("/")[0] + "/" if namelist else ""

                for file_info in z.infolist():
                    if file_info.is_dir():
                        continue

                    # Strip root prefix
                    rel_path = file_info.filename
                    if rel_path.startswith(root_prefix):
                        rel_path = rel_path[len(root_prefix):]

                    if not rel_path:
                        continue

                    safe_path = sanitize_relative_path(rel_path)
                    file_size = file_info.file_size

                    # Eligibility check
                    is_eligible, _ = is_eligible_source_file(
                        file_path=safe_path,
                        file_size_bytes=file_size,
                        max_size_kb=settings.MAX_FILE_SIZE_KB,
                    )
                    if not is_eligible:
                        continue

                    # Read content
                    raw_content = z.read(file_info.filename)
                    if is_binary_content(raw_content):
                        continue

                    try:
                        text_content = raw_content.decode("utf-8")
                    except UnicodeDecodeError:
                        try:
                            text_content = raw_content.decode("latin-1")
                        except Exception:
                            continue

                    language = get_file_language(safe_path) or "text"
                    lines = text_content.splitlines()
                    line_count = len(lines)

                    # AST / Symbol extraction
                    ast_symbols = []
                    if language == "python":
                        ast_data = parse_python_ast(text_content)
                        ast_symbols = ast_data.get("symbols", [])
                    elif language in ("javascript", "typescript", "java", "go"):
                        ast_symbols = parse_generic_symbols(text_content, language)

                    # Persist local file copy for Code Explorer and Analysis
                    local_repo_dir = settings.DATA_DIR / "repos" / repo_id
                    cached_file_path = local_repo_dir / safe_path
                    cached_file_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        cached_file_path.write_text(text_content, encoding="utf-8")
                    except Exception:
                        pass

                    file_records.append(
                        RepoFile(
                            repository_id=repo_id,
                            path=safe_path,
                            language=language,
                            size_bytes=file_size,
                            line_count=line_count,
                            ast_symbols_json=json.dumps(ast_symbols),
                        )
                    )

                    # Chunking
                    chunks = chunk_code_file(
                        content=text_content,
                        file_path=safe_path,
                        repository_id=repo_id,
                        language=language,
                        chunk_size_chars=settings.CHUNK_SIZE,
                        chunk_overlap_chars=settings.CHUNK_OVERLAP,
                    )
                    all_chunks.extend(chunks)
                    scanned_count += 1

                    if scanned_count >= settings.MAX_REPO_FILES:
                        logger.warning(f"Reached MAX_REPO_FILES limit of {settings.MAX_REPO_FILES}")
                        break

                # Persist files to SQLite
                db.add_all(file_records)

                # Persist chunks to ChromaDB
                indexed_chunk_count = self.vector_store.add_chunks(repo_id, all_chunks)

                # Update repo record
                repo_record.file_count = len(file_records)
                repo_record.chunk_count = indexed_chunk_count
                repo_record.status = "ready"
                repo_record.error_message = None
                await db.commit()
                await db.refresh(repo_record)

                return repo_record

        except Exception as e:
            logger.exception("Ingestion failed")
            repo_record.status = "failed"
            repo_record.error_message = str(e)
            await db.commit()
            raise IngestionError(f"Repository indexing failed: {e}")


ingestion_service = RepositoryIngestionService()
