"""SQLAlchemy database models for CodeMind AI."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Repository(Base):
    """Indexed GitHub repository metadata."""
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    url: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    owner: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    default_branch: Mapped[str] = mapped_column(String(128), default="main")
    commit_sha: Mapped[str] = mapped_column(String(64), default="")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    primary_language: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, indexing, ready, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    files: Mapped[list["RepoFile"]] = relationship("RepoFile", back_populates="repository", cascade="all, delete-orphan")


class RepoFile(Base):
    """Source code file metadata within an indexed repository."""
    __tablename__ = "repository_files"

    id: Mapped[str] = mapped_column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id: Mapped[str] = mapped_column(String(128), ForeignKey("repositories.id", ondelete="CASCADE"), index=True)
    path: Mapped[str] = mapped_column(String(512), index=True)
    language: Mapped[str] = mapped_column(String(64), default="text")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    line_count: Mapped[int] = mapped_column(Integer, default=0)
    ast_symbols_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-encoded AST symbols

    repository: Mapped["Repository"] = relationship("Repository", back_populates="files")


class BenchmarkRecord(Base):
    """Developer velocity benchmarking entry (Manual vs AI-Assisted)."""
    __tablename__ = "benchmark_records"

    id: Mapped[str] = mapped_column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_name: Mapped[str] = mapped_column(String(256), index=True)
    workflow_type: Mapped[str] = mapped_column(String(32))  # "Manual" or "AI-Assisted"
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    tests_run: Mapped[int] = mapped_column(Integer, default=0)
    tests_passed: Mapped[int] = mapped_column(Integer, default=0)
    review_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    corrections_required: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
