"""lingwen-full-check-report — canonical full-check report package.

Phase 48 P3-ARCHDEBT: relocated from infra/full_check_report.py (287 LOC).
NOT-LEAF (2 workspace deps: lingwen-paths + lingwen-quality).
"""

from __future__ import annotations

from lingwen_full_check_report.service import (
    collect_full_check_issues,
    collect_prose_vitality_scores,
    format_report_markdown,
    generate_report,
    load_report_summary,
    parse_report_markdown,
    report_path_for,
)

__all__ = [
    "report_path_for",
    "collect_prose_vitality_scores",
    "collect_full_check_issues",
    "format_report_markdown",
    "generate_report",
    "parse_report_markdown",
    "load_report_summary",
]