"""Backward-compat shim — canonical module is `lingwen_studio_registry` (Phase 40a P3-ARCHDEBT).

See invariant #55. Scheduled for deletion in Phase 40b after `tests/` migration.
"""
from lingwen_studio_registry import *  # noqa: F401,F403

__all__ = [  # noqa: F405
    "StudioProject",
    "factory_root",
    "list_projects",
    "get_project_by_slug",
    "active_state_path",
    "read_active_slug",
    "activate_project",
    "active_project",
    "pilot_records_dir_for",
    "project_summary",
    "quality_summary",
    "production_preflight",
    "find_calibration_batch",
    "suggest_batch_budget_usd",
    "batch_command",
    "quality_report_summary",
    "prose_diff_summary",
    "prose_judge_summary",
]
