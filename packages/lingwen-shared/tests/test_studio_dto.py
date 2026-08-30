"""Contract regression tests for v16.5 #N.7 lingwen-shared studio contracts.

Promoted from manual TS DTOs (packages/dashboard-contracts/src/shared/studio.ts).
23 Pydantic models.
"""
from __future__ import annotations

import pytest


def test_studio_dtos_importable() -> None:
    """All studio DTOs must import from lingwen_shared.contracts.python.studio."""
    from lingwen_shared.contracts.python.studio import (  # noqa: F401
        StudioActiveResponse,
        StudioBatchJobResponse,
        StudioBatchRunRequest,
        StudioPreflightChapter,
        StudioPreflightRequest,
        StudioPreflightResponse,
        StudioProjectItem,
        StudioProjectsResponse,
        StudioProseDiffChapter,
        StudioProseDiffResponse,
        StudioProseDiffTotals,
        StudioProseHeatmap,
        StudioProseHeatmapChapter,
        StudioProseJudgeChapter,
        StudioProseJudgeRating,
        StudioProseJudgeResponse,
        StudioProseJudgeSignal,
        StudioQualityReportChapter,
        StudioQualityReportIssue,
        StudioQualityReportResponse,
        StudioQualityResponse,
        StudioSetActiveRequest,
        StudioSummaryResponse,
    )


def test_studio_summary_defaults() -> None:
    """StudioSummaryResponse default values."""
    from lingwen_shared.contracts.python.studio import StudioSummaryResponse
    obj = StudioSummaryResponse(
        slug="x", name="X", role="studio", root="/x", location="/x",
        max_chapter=10, genre="scifi", chapter_count=5, latest_chapter=5,
        outline_count=5, golden_chapters=[1, 2], has_golden_set=True,
        pilot_records_dir="/x", pilot_record_count=0, pillars_ok=True,
        pillars_path="/x",
    )
    assert obj.creation_mode == "studio"
    assert obj.quality_profile == "studio_full"


def test_studio_prose_diff_response_default_totals() -> None:
    """StudioProseDiffResponse default total_delta=None, chapters=[]."""
    from lingwen_shared.contracts.python.studio import StudioProseDiffResponse
    obj = StudioProseDiffResponse(
        slug="x", available=False, snapshot_path="/x",
    )
    assert obj.total_delta is None
    assert obj.chapters == []
    assert obj.net_prose_p1_delta == 0


def test_studio_batch_run_request_ge_constraints() -> None:
    """StudioBatchRunRequest start_chapter/end_chapter ge=1; budget_usd ge=0,le=100."""
    from lingwen_shared.contracts.python.studio import StudioBatchRunRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        StudioBatchRunRequest(start_chapter=0, end_chapter=5)
    with pytest.raises(ValidationError):
        StudioBatchRunRequest(start_chapter=1, end_chapter=5, budget_usd=200.0)
    obj = StudioBatchRunRequest(start_chapter=1, end_chapter=5)
    assert obj.budget_usd == 0.15  # default


def test_studio_prose_judge_response_defaults() -> None:
    """StudioProseJudgeResponse default lists=[]."""
    from lingwen_shared.contracts.python.studio import StudioProseJudgeResponse
    obj = StudioProseJudgeResponse(slug="x", available=False)
    assert obj.chapters == []
    assert obj.golden_chapters == []
    assert obj.weighted_avg == 0.0
