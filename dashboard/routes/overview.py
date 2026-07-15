"""
Phase 15.0 T1.4: overview / chapters / production-records routes.

Extracted from dashboard/app.py create_app closure (was at app.py lines 248-369).
"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from dashboard.helpers.production_records import production_records_root
from dashboard.models import (
    ChapterData,
    ChaptersResponse,
    OverviewResponse,
    ProductionBatchRollupResponse,
    ProductionCostTrendResponse,
    ProductionRecordResponse,
    ProductionRecordsResponse,
    ProductionRollupResponse,
)
from dashboard.routes.ctx import RoutesContext


def register_overview(app: FastAPI, ctx: RoutesContext) -> None:
    @app.get("/api/overview", response_model=OverviewResponse)
    def get_overview() -> OverviewResponse:
        """Get overview statistics from reading_power.db."""
        if not ctx.db.exists():
            return OverviewResponse(
                total_chapters=0,
                total_hooks=0,
                avg_hook_strength=0.0,
                total_coolpoints=0,
                avg_coolpoint_density=0.0,
            )
        if ctx.db.is_empty():
            return OverviewResponse(
                total_chapters=0,
                total_hooks=0,
                avg_hook_strength=0.0,
                total_coolpoints=0,
                avg_coolpoint_density=0.0,
            )

        stats = ctx.db.get_overview_stats()
        if stats is None:
            return OverviewResponse(
                total_chapters=0,
                total_hooks=0,
                avg_hook_strength=0.0,
                total_coolpoints=0,
                avg_coolpoint_density=0.0,
            )

        return OverviewResponse(
            total_chapters=stats["total_chapters"],
            total_hooks=stats["total_hooks"],
            avg_hook_strength=stats["avg_hook_strength"],
            total_coolpoints=stats["total_coolpoints"],
            avg_coolpoint_density=stats["avg_coolpoint_density"],
        )

    @app.get("/api/chapters", response_model=ChaptersResponse)
    def get_chapters(range: str = "1-30") -> ChaptersResponse:
        """
        Get chapter data for a specified range.

        Args:
            range: Chapter range in format "start-end" (e.g., "1-30")
        """
        try:
            parts = range.split("-")
            if len(parts) != 2:
                raise ValueError("Range must be in format 'start-end'")
            start_chapter = int(parts[0])
            end_chapter = int(parts[1])
            if start_chapter > end_chapter:
                raise ValueError("Start chapter must be <= end chapter")
        except (ValueError, IndexError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid range parameter: {range}. Use format '1-30'. Error: {e}",
            )

        if not ctx.db.exists():
            return ChaptersResponse(chapters=[])

        chapters = ctx.db.get_chapters_range(start_chapter, end_chapter)
        return ChaptersResponse(
            chapters=[
                ChapterData(
                    chapter=ch["chapter"],
                    hook_count=ch["hook_count"],
                    hook_strength_avg=ch["hook_strength_avg"],
                    coolpoint_count=ch["coolpoint_count"],
                    coolpoint_density=ch["coolpoint_density"],
                )
                for ch in chapters
            ]
        )

    @app.get("/api/production-records", response_model=ProductionRecordsResponse)
    def get_production_records(
        chapter_num: Optional[int] = Query(default=None, ge=1),
        limit: int = Query(default=30, ge=1, le=100),
    ) -> ProductionRecordsResponse:
        """Phase 9.82 F74: read pilot/batch JSON from infra/.state/pilot_records."""
        from infra.agent_system.production_records import (
            list_production_records,
        )

        root = production_records_root()
        items = list_production_records(root, chapter_num=chapter_num, limit=limit)
        return ProductionRecordsResponse(
            records_dir=str(root),
            records=[
                ProductionRecordResponse(**item.to_dict()) for item in items
            ],
        )

    @app.get("/api/production-records/rollup", response_model=ProductionRollupResponse)
    def get_production_records_rollup(
        limit: int = Query(default=100, ge=1, le=200),
    ) -> ProductionRollupResponse:
        """Phase 9.89 F81: deduplicated cost + batch list for Analytics."""
        from infra.agent_system.production_records import (
            rollup_production_records,
        )

        data = rollup_production_records(production_records_root(), limit=limit)
        return ProductionRollupResponse(
            **{
                **data,
                "batches": [
                    ProductionBatchRollupResponse(**row) for row in data["batches"]
                ],
            }
        )

    @app.get("/api/production-records/trend", response_model=ProductionCostTrendResponse)
    def get_production_records_trend(
        limit: int = Query(default=100, ge=1, le=200),
    ) -> ProductionCostTrendResponse:
        """Phase 9.96 F87: time-ordered cost trend for Analytics mini chart."""
        from infra.agent_system.production_records import (
            production_cost_trend,
        )

        return ProductionCostTrendResponse(
            **production_cost_trend(production_records_root(), limit=limit)
        )
