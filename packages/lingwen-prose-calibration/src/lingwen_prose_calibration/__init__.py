"""lingwen-prose-calibration — canonical prose calibration package.

Phase 44 P3-ARCHDEBT: relocated from infra/prose_calibration.py (191 LOC).
TRUE LEAF (0 workspace deps; PyYAML>=6.0 3rd-party only).
"""

from __future__ import annotations

from lingwen_prose_calibration.service import (
    build_prose_heatmap,
    evaluate_against_baseline,
    format_calibration_report,
    is_primary_revision_slug,
    is_prose_issue,
    list_primary_revision_slugs,
    load_prose_config,
    resolve_llm_post_check,
)

__all__ = [
    "load_prose_config",
    "is_prose_issue",
    "build_prose_heatmap",
    "evaluate_against_baseline",
    "format_calibration_report",
    "list_primary_revision_slugs",
    "is_primary_revision_slug",
    "resolve_llm_post_check",
]