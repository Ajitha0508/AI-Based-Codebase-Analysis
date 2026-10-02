"""Pydantic request and response models for CodeMind AI API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --- Health & Settings ---
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    active_llm_provider: str
    active_embedding_provider: str
    chroma_db_status: str


class SettingsStatusResponse(BaseModel):
    llm_provider: str
    llm_model: str
    is_gemini_configured: bool
    is_openai_configured: bool
    is_groq_configured: bool
    embedding_provider: str
    chunk_size: int
    chunk_overlap: int
    retrieval_top_k: int
    max_file_size_kb: int


# --- Repositories ---
class IndexRepoRequest(BaseModel):
    url: str = Field(..., description="Public GitHub repository URL, e.g. https://github.com/owner/repo")
    force_refresh: bool = Field(False, description="Force re-indexing even if commit SHA hasn't changed")


class RepositoryResponse(BaseModel):
    id: str
    url: str
    owner: str
    name: str
    default_branch: str
    commit_sha: str
    description: Optional[str] = None
    primary_language: Optional[str] = None
    file_count: int
    chunk_count: int
    status: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RepoFileResponse(BaseModel):
    id: str
    repository_id: str
    path: str
    language: str
    size_bytes: int
    line_count: int
    ast_symbols: Optional[List[Dict[str, Any]]] = None


class FileContentResponse(BaseModel):
    repository_id: str
    file_path: str
    language: str
    line_count: int
    content: str
    ast_symbols: Optional[List[Dict[str, Any]]] = None


# --- RAG Chat ---
class ChatRequest(BaseModel):
    repository_id: str
    query: str
    top_k: Optional[int] = 5


class SourceReference(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    content: str
    similarity: float
    symbol_name: Optional[str] = ""
    language: Optional[str] = ""


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceReference]
    supporting_files_summary: List[str]
    insufficient_evidence: bool = False


# --- Code Review ---
class CodeReviewRequest(BaseModel):
    repository_id: str
    file_path: str
    code_override: Optional[str] = None


class ReviewFinding(BaseModel):
    title: str
    severity: str  # Critical, High, Medium, Low
    category: str
    file_path: str
    line_range: str
    explanation: str
    why_it_matters: str
    suggested_fix: str
    verification_status: str
    human_review_required: bool = True


class CodeReviewResponse(BaseModel):
    file_path: str
    language: str
    total_findings: int
    severity_counts: Dict[str, int]
    findings: List[ReviewFinding]
    human_review_notice: str


# --- Test Generation ---
class TestGenRequest(BaseModel):
    repository_id: str
    file_path: str
    symbol_name: Optional[str] = None


class TestGenResponse(BaseModel):
    file_path: str
    language: str
    framework: str
    target_symbol: Optional[str]
    generated_test_code: str
    discovered_symbols: List[str]
    assumptions: List[str]
    execution_note: str


# --- Documentation Generation ---
class DocGenRequest(BaseModel):
    repository_id: str
    doc_type: str = Field("overview", description="'overview', 'module', 'api', 'setup', 'readme'")


class DocGenResponse(BaseModel):
    doc_type: str
    repo_name: str
    markdown_content: str


# --- Velocity Benchmarking ---
class BenchmarkCreateRequest(BaseModel):
    task_name: str
    workflow_type: str  # "Manual" or "AI-Assisted"
    duration_seconds: float
    tests_run: int = 0
    tests_passed: int = 0
    review_findings_count: int = 0
    corrections_required: int = 0
    notes: Optional[str] = ""


class BenchmarkMetricsResponse(BaseModel):
    summary: Dict[str, Any]
    manual_metrics: Dict[str, Any]
    ai_metrics: Dict[str, Any]
    task_comparisons: List[Dict[str, Any]]
    records: List[Dict[str, Any]]
    methodology_note: str
