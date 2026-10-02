"""Developer velocity benchmarking endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.codemind_schemas import BenchmarkCreateRequest, BenchmarkMetricsResponse
from app.services.benchmark_service import benchmark_service

router = APIRouter(prefix="/benchmarks", tags=["Benchmarking"])


@router.get("", response_model=BenchmarkMetricsResponse)
async def get_benchmarks(db: AsyncSession = Depends(get_db)):
    """Retrieve velocity metrics, comparisons, and recorded benchmark runs."""
    metrics = await benchmark_service.get_aggregated_metrics(db)
    return BenchmarkMetricsResponse(**metrics)


@router.post("", status_code=status.HTTP_201_CREATED)
async def record_benchmark(
    request: BenchmarkCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Record a real developer task execution (Manual vs AI-Assisted)."""
    if request.workflow_type not in ("Manual", "AI-Assisted"):
        raise HTTPException(
            status_code=400,
            detail="Workflow type must be strictly 'Manual' or 'AI-Assisted'."
        )

    rec = await benchmark_service.add_record(
        db=db,
        task_name=request.task_name,
        workflow_type=request.workflow_type,
        duration_seconds=request.duration_seconds,
        tests_run=request.tests_run,
        tests_passed=request.tests_passed,
        review_findings_count=request.review_findings_count,
        corrections_required=request.corrections_required,
        notes=request.notes or "",
        is_sample=False,
    )

    return {
        "message": "Benchmark entry recorded successfully.",
        "id": rec.id,
        "task_name": rec.task_name,
        "workflow_type": rec.workflow_type,
    }
