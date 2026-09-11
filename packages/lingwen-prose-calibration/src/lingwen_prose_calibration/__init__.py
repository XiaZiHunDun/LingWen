"""lingwen-prose-calibration — canonical prose calibration package.

Phase 44 P3-ARCHDEBT: relocated from infra/prose_calibration.py (191 LOC).
Phase 51 P3-ARCHDEBT: MERGED with infra/prose_calibration_overrides.py (174 LOC, 9 funcs).
TRUE LEAF (0 workspace deps; PyYAML>=6.0 3rd-party only).
"""

from __future__ import annotations

from lingwen_prose_calibration.overrides import (
    apply_calibration_overrides,
    default_overrides_path,
    load_all_calibration_overrides,
    load_yaml_overrides,
    merge_calibration_overrides,
    override_key,
    parse_markdown_log_overrides,
    parse_override_key,
    save_yaml_override,
)
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
    # service (Phase 44)
    "load_prose_config",
    "is_prose_issue",
    "build_prose_heatmap",
    "evaluate_against_baseline",
    "format_calibration_report",
    "list_primary_revision_slugs",
    "is_primary_revision_slug",
    "resolve_llm_post_check",
    # overrides (Phase 51 MERGE)
    "apply_calibration_overrides",
    "default_overrides_path",
    "load_all_calibration_overrides",
    "load_yaml_overrides",
    "merge_calibration_overrides",
    "override_key",
    "parse_markdown_log_overrides",
    "parse_override_key",
    "save_yaml_override",
]
