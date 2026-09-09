"""Canonical LingWen Studio project registry API."""

from lingwen_studio_registry.discovery import (
    _load_yaml_project,
    factory_root,
    get_project_by_slug,
    list_projects,
)
from lingwen_studio_registry.models import (
    _ACTIVE_STATE,
    _CHAPTER_RE,
    _OUTLINE_RE,
    StudioProject,
)
from lingwen_studio_registry.reports import (
    prose_diff_summary,
    prose_judge_summary,
    quality_report_summary,
)
from lingwen_studio_registry.state import (
    activate_project,
    active_project,
    active_state_path,
    read_active_slug,
)
from lingwen_studio_registry.summary import (
    _chapter_nums,
    _outline_nums,
    batch_command,
    find_calibration_batch,
    pilot_records_dir_for,
    production_preflight,
    project_summary,
    quality_summary,
    suggest_batch_budget_usd,
)

__all__ = [
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
