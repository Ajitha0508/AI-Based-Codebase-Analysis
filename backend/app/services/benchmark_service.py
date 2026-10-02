"""Developer velocity benchmarking service: records, metrics, and comparisons."""

from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BenchmarkRecord


class BenchmarkService:
    """Computes real velocity comparisons and aggregates between Manual and AI-Assisted workflows."""

    async def get_all_records(self, db: AsyncSession) -> List[BenchmarkRecord]:
        """Fetch all benchmark runs ordered by created date."""
        stmt = select(BenchmarkRecord).order_by(BenchmarkRecord.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def add_record(
        self,
        db: AsyncSession,
        task_name: str,
        workflow_type: str,
        duration_seconds: float,
        tests_run: int = 0,
        tests_passed: int = 0,
        review_findings_count: int = 0,
        corrections_required: int = 0,
        notes: str = "",
        is_sample: bool = False,
    ) -> BenchmarkRecord:
        """Record a live benchmark task measurement."""
        rec = BenchmarkRecord(
            task_name=task_name.strip(),
            workflow_type=workflow_type.strip(),
            duration_seconds=max(0.0, float(duration_seconds)),
            tests_run=max(0, int(tests_run)),
            tests_passed=max(0, int(tests_passed)),
            review_findings_count=max(0, int(review_findings_count)),
            corrections_required=max(0, int(corrections_required)),
            notes=notes.strip() if notes else None,
            is_sample=is_sample,
        )
        db.add(rec)
        await db.commit()
        await db.refresh(rec)
        return rec

    async def get_aggregated_metrics(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Compute comparative velocity metrics grouped by workflow type and task name.
        """
        records = await self.get_all_records(db)

        manual_records = [r for r in records if r.workflow_type.lower() == "manual"]
        ai_records = [r for r in records if r.workflow_type.lower() == "ai-assisted"]

        def calc_stats(recs: List[BenchmarkRecord]) -> Dict[str, Any]:
            if not recs:
                return {
                    "count": 0,
                    "avg_duration_seconds": 0.0,
                    "avg_duration_minutes": 0.0,
                    "total_tests_run": 0,
                    "total_tests_passed": 0,
                    "test_pass_rate_pct": 0.0,
                    "total_review_findings": 0,
                    "total_corrections_required": 0,
                }
            tot_sec = sum(r.duration_seconds for r in recs)
            tot_tests = sum(r.tests_run for r in recs)
            tot_passed = sum(r.tests_passed for r in recs)
            pass_rate = (tot_passed / tot_tests * 100.0) if tot_tests > 0 else 0.0

            return {
                "count": len(recs),
                "avg_duration_seconds": round(tot_sec / len(recs), 1),
                "avg_duration_minutes": round((tot_sec / len(recs)) / 60.0, 1),
                "total_tests_run": tot_tests,
                "total_tests_passed": tot_passed,
                "test_pass_rate_pct": round(pass_rate, 1),
                "total_review_findings": sum(r.review_findings_count for r in recs),
                "total_corrections_required": sum(r.corrections_required for r in recs),
            }

        manual_stats = calc_stats(manual_records)
        ai_stats = calc_stats(ai_records)

        # Calculate time difference and percentage improvement
        time_saved_seconds = 0.0
        pct_improvement = 0.0
        if manual_stats["avg_duration_seconds"] > 0 and ai_stats["avg_duration_seconds"] > 0:
            time_saved_seconds = manual_stats["avg_duration_seconds"] - ai_stats["avg_duration_seconds"]
            pct_improvement = (time_saved_seconds / manual_stats["avg_duration_seconds"]) * 100.0

        # Group by task for side-by-side comparison
        tasks_map: Dict[str, Dict[str, Any]] = {}
        for r in records:
            if r.task_name not in tasks_map:
                tasks_map[r.task_name] = {"task_name": r.task_name, "manual": None, "ai": None}
            entry = {
                "duration_seconds": r.duration_seconds,
                "duration_minutes": round(r.duration_seconds / 60.0, 1),
                "tests_run": r.tests_run,
                "tests_passed": r.tests_passed,
                "corrections": r.corrections_required,
                "is_sample": r.is_sample,
            }
            if r.workflow_type.lower() == "manual":
                tasks_map[r.task_name]["manual"] = entry
            else:
                tasks_map[r.task_name]["ai"] = entry

        task_comparisons = list(tasks_map.values())

        return {
            "summary": {
                "total_recorded_runs": len(records),
                "manual_runs_count": len(manual_records),
                "ai_runs_count": len(ai_records),
                "time_saved_seconds_avg": round(time_saved_seconds, 1),
                "time_saved_minutes_avg": round(time_saved_seconds / 60.0, 1),
                "speedup_percentage": round(pct_improvement, 1),
            },
            "manual_metrics": manual_stats,
            "ai_metrics": ai_stats,
            "task_comparisons": task_comparisons,
            "records": [
                {
                    "id": r.id,
                    "task_name": r.task_name,
                    "workflow_type": r.workflow_type,
                    "duration_seconds": r.duration_seconds,
                    "duration_minutes": round(r.duration_seconds / 60.0, 1),
                    "tests_run": r.tests_run,
                    "tests_passed": r.tests_passed,
                    "review_findings_count": r.review_findings_count,
                    "corrections_required": r.corrections_required,
                    "notes": r.notes,
                    "is_sample": r.is_sample,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ],
            "methodology_note": (
                "Metrics represent actual recorded measurements across tasks. "
                "Sample entries are explicitly tagged with `is_sample: true`."
            )
        }


benchmark_service = BenchmarkService()
