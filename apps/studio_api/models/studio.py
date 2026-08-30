"""Re-export from lingwen-shared canonical models.

Phase 126 v16.5 #N.9: Studio models are now thin re-exports of
``packages/lingwen-shared/src/lingwen_shared/contracts/python/studio.py``.
The canonical Pydantic v2 source-of-truth lives in lingwen-shared.

Includes 23 Pydantic models covering the dashboard surface of the studio
API: projects, active, summary, quality, quality-report, prose-heatmap,
prose-diff, prose-judge, preflight, batch-run, batch-job.
"""
from lingwen_shared.contracts.python.studio import (
    StudioProjectItem,
    StudioProjectsResponse,
    StudioActiveResponse,
    StudioSetActiveRequest,
    StudioSummaryResponse,
    StudioQualityResponse,
    StudioQualityReportIssue,
    StudioQualityReportChapter,
    StudioProseHeatmapChapter,
    StudioProseHeatmap,
    StudioQualityReportResponse,
    StudioProseDiffTotals,
    StudioProseDiffChapter,
    StudioProseDiffResponse,
    StudioProseJudgeRating,
    StudioProseJudgeChapter,
    StudioProseJudgeSignal,
    StudioProseJudgeResponse,
    StudioPreflightChapter,
    StudioPreflightRequest,
    StudioPreflightResponse,
    StudioBatchRunRequest,
    StudioBatchJobResponse,
)

__all__ = [
    "StudioProjectItem",
    "StudioProjectsResponse",
    "StudioActiveResponse",
    "StudioSetActiveRequest",
    "StudioSummaryResponse",
    "StudioQualityResponse",
    "StudioQualityReportIssue",
    "StudioQualityReportChapter",
    "StudioProseHeatmapChapter",
    "StudioProseHeatmap",
    "StudioQualityReportResponse",
    "StudioProseDiffTotals",
    "StudioProseDiffChapter",
    "StudioProseDiffResponse",
    "StudioProseJudgeRating",
    "StudioProseJudgeChapter",
    "StudioProseJudgeSignal",
    "StudioProseJudgeResponse",
    "StudioPreflightChapter",
    "StudioPreflightRequest",
    "StudioPreflightResponse",
    "StudioBatchRunRequest",
    "StudioBatchJobResponse",
]
