"""Contract regression tests for v16.5 #N.7 lingwen-shared health contracts.

Promoted from manual TS DTOs (packages/dashboard-contracts/src/shared/health.ts).
12 Pydantic models.

Verifies:
- All health DTOs importable from lingwen_shared.contracts.python.health
- Each DTO can be constructed with required fields
- Pydantic v2 validation enforces types (extra='ignore', Optional defaults)
"""
from __future__ import annotations


def test_health_dtos_importable() -> None:
    """All health DTOs must import from lingwen_shared.contracts.python.health."""
    from lingwen_shared.contracts.python.health import (  # noqa: F401
        ChapterData,
        ChaptersResponse,
        DatabaseStatus,
        HealthResponse,
        MemoryUsage,
        OverviewResponse,
        ProductionBatchRollupResponse,
        ProductionCostTrendPointResponse,
        ProductionCostTrendResponse,
        ProductionRecordResponse,
        ProductionRecordsResponse,
        ProductionRollupResponse,
    )


def test_database_status_basic_shape() -> None:
    """DatabaseStatus accepts status + optional fields."""
    from lingwen_shared.contracts.python.health import DatabaseStatus
    obj = DatabaseStatus(status="ok", error=None, tables=42, records=1000)
    assert obj.status == "ok"
    assert obj.tables == 42


def test_health_response_full_shape() -> None:
    """HealthResponse nested models."""
    from lingwen_shared.contracts.python.health import (
        DatabaseStatus,
        HealthResponse,
        MemoryUsage,
    )
    hr = HealthResponse(
        status="ok",
        service="studio",
        timestamp="2026-08-30T00:00:00Z",
        uptime=100.0,
        version="16.5",
        python_version="3.13",
        database=DatabaseStatus(status="ok"),
        memory=MemoryUsage(rss_mb=100.0, vms_mb=200.0, cpu_percent=5.0, num_threads=8),
    )
    assert hr.status == "ok"
    assert hr.memory.num_threads == 8


def test_overview_response_shape() -> None:
    """OverviewResponse numeric fields."""
    from lingwen_shared.contracts.python.health import OverviewResponse
    obj = OverviewResponse(
        total_chapters=100,
        total_hooks=500,
        avg_hook_strength=0.75,
        total_coolpoints=300,
        avg_coolpoint_density=3.0,
    )
    assert obj.total_chapters == 100


def test_chapters_response_nested() -> None:
    """ChaptersResponse contains list of ChapterData."""
    from lingwen_shared.contracts.python.health import ChapterData, ChaptersResponse
    obj = ChaptersResponse(chapters=[ChapterData(
        chapter=1, hook_count=5, hook_strength_avg=0.8,
        coolpoint_count=3, coolpoint_density=2.5,
    )])
    assert len(obj.chapters) == 1
    assert obj.chapters[0].chapter == 1


def test_production_rollup_response_shape() -> None:
    """ProductionRollupResponse default batches=[]."""
    from lingwen_shared.contracts.python.health import ProductionRollupResponse
    obj = ProductionRollupResponse(
        records_dir="/x", record_count=1, pilot_count=1, batch_count=0,
        total_cost_usd=0.5, chapters_with_records=10, batches=[],
    )
    assert obj.batch_count == 0


def test_production_rollup_response_latest_recorded_at() -> None:
    """ProductionRollupResponse.latest_recorded_at accepts ISO string."""
    from lingwen_shared.contracts.python.health import ProductionRollupResponse
    obj = ProductionRollupResponse(
        records_dir="/x", record_count=1, pilot_count=1, batch_count=0,
        total_cost_usd=0.5, chapters_with_records=10, batches=[],
        latest_recorded_at="2026-08-30T00:00:00Z",
    )
    assert obj.latest_recorded_at == "2026-08-30T00:00:00Z"


def test_extra_fields_ignored() -> None:
    """extra='ignore' allows unknown fields (forward compat)."""
    from lingwen_shared.contracts.python.health import OverviewResponse
    obj = OverviewResponse(
        total_chapters=1, total_hooks=1, avg_hook_strength=0.5,
        total_coolpoints=1, avg_coolpoint_density=0.5,
        unknown_field="x",  # type: ignore[call-arg]
    )
    assert obj.total_chapters == 1
    assert not hasattr(obj, "unknown_field")
