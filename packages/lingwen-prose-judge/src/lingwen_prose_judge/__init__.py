"""lingwen-prose-judge — canonical prose judge package.

Phase 51 P3-ARCHDEBT: relocated from infra/prose_judge.py (734 LOC, 28 symbols).
NOT-LEAF (4 workspace deps: lingwen-prose-calibration + lingwen-llm +
lingwen-shared + lingwen-full-check-report).

Public surface: 7 consts + 21 funcs (28 total). Explicit `__all__` keeps
wildcard re-exports contained — see Phase 42 lesson on smoke test that
asserts `len(__all__) == 28`.
"""

from __future__ import annotations

from lingwen_prose_judge.analysis import cross_reference_signals, summarize_judge_report
from lingwen_prose_judge.calibration import (
    build_calibration_round,
    compute_misreport_stats,
    fill_calibration_samples,
    format_calibration_sample_markdown,
    render_calibration_log_document,
    sample_calibration_pack,
    suggest_calibration_verdict,
)
from lingwen_prose_judge.constants import (
    ACTIONS,
    DIMENSIONS,
    DIMENSION_LABELS,
    ISSUE_TYPE_TO_DIMENSION,
    JUDGE_REPORT_VERSION,
    JUDGE_SYSTEM_PROMPT,
    REPORT_FILENAME,
)
from lingwen_prose_judge.ratings import (
    build_llm_judge_report,
    build_offline_judge_report,
    derive_offline_chapter_ratings,
    run_prose_judge,
)
from lingwen_prose_judge.report_io import (
    golden_chapter_path,
    golden_manifest_path,
    load_golden_chapter_nums,
    load_judge_report,
    map_issue_type_to_dimension,
    report_path_for,
    save_judge_report,
    validate_judge_report,
)

__all__ = [
    # constants (7)
    "ACTIONS",
    "DIMENSIONS",
    "DIMENSION_LABELS",
    "ISSUE_TYPE_TO_DIMENSION",
    "JUDGE_REPORT_VERSION",
    "JUDGE_SYSTEM_PROMPT",
    "REPORT_FILENAME",
    # report_io (7)
    "report_path_for",
    "golden_manifest_path",
    "golden_chapter_path",
    "load_golden_chapter_nums",
    "load_judge_report",
    "save_judge_report",
    "map_issue_type_to_dimension",
    "validate_judge_report",
    # ratings (4)
    "derive_offline_chapter_ratings",
    "build_offline_judge_report",
    "build_llm_judge_report",
    "run_prose_judge",
    # analysis (2)
    "cross_reference_signals",
    "summarize_judge_report",
    # calibration (7)
    "sample_calibration_pack",
    "format_calibration_sample_markdown",
    "suggest_calibration_verdict",
    "fill_calibration_samples",
    "compute_misreport_stats",
    "build_calibration_round",
    "render_calibration_log_document",
]
