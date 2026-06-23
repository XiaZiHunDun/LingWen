"""Auto-detect onboarding wizard step completion from project artifacts."""
from __future__ import annotations

from infra.creator_volume_plan import load_volume_plan, volume_plan_state_path
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig
from infra.studio_registry import StudioProject, quality_report_summary

_PILLARS_MIN_CHARS = 60


def infer_auto_completed_steps(project: StudioProject) -> list[str]:
    """Return step ids that appear satisfied by files on disk."""
    paths = ProjectPaths.get(project.root)
    config = ProjectConfig.load(paths)
    inferred: list[str] = ["init", "dashboard"]

    if config.pillars_path.is_file():
        text = config.pillars_path.read_text(encoding="utf-8").strip()
        if len(text) >= _PILLARS_MIN_CHARS:
            inferred.append("pillars")

    volumes = load_volume_plan(project.root)
    if volumes and (
        any(v.locked for v in volumes)
        or volume_plan_state_path(project.root).is_file()
    ):
        inferred.append("volume")

    scan_upto = min(config.max_chapter, 30)
    if any(bool(paths.read_chapter(n)) for n in range(1, scan_upto + 1)):
        inferred.append("write")

    docs_dir = project.root / "docs"
    if docs_dir.is_dir() and list(docs_dir.glob("volume-summary-ch*.md")):
        inferred.append("check")

    report = quality_report_summary(project)
    if report.get("available") and int(report.get("p0") or 1) == 0:
        if "check" not in inferred:
            inferred.append("check")

    return inferred
