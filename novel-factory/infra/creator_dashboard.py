"""Creator dashboard data (companion / advance overview)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from infra.creator_mode import settings_from_project_config
from infra.creator_ui_profile import ui_profile_from_project_config
from infra.creator_volume_pulse import build_volume_pulse
from infra.creator_volume_plan import load_volume_plan, compute_volume_deviations
from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig
from infra.studio_registry import StudioProject, quality_report_summary


def _excerpt(text: str, *, limit: int = 280) -> str:
    compact = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "…"


def creator_overview(project: StudioProject) -> dict[str, Any]:
    paths = ProjectPaths.get(project.root)
    config = ProjectConfig.load(paths)
    settings = settings_from_project_config(config)
    chapters_dir = project.root / "03_内容仓库" / "04_正文"
    global_outline = project.root / "03_内容仓库" / "01_全文总体大纲" / "全局大纲.md"

    chapter_rows: list[dict[str, Any]] = []
    for num in range(1, config.max_chapter + 1):
        body = paths.read_chapter(num)
        outline = config.chapter_outline_path(num, paths)
        chapter_rows.append(
            {
                "chapter": num,
                "has_body": bool(body),
                "has_outline": outline.is_file(),
                "word_count": len(re.sub(r"\s+", "", body)) if body else 0,
                "excerpt": _excerpt(body) if body else None,
            },
        )

    written = sum(1 for row in chapter_rows if row["has_body"])
    volume_docs = sorted(
        (project.root / "docs").glob("volume-summary-ch*.md"),
        key=lambda p: p.name,
    ) if (project.root / "docs").is_dir() else []
    volume_summaries = [
        {
            "path": str(p),
            "name": p.name,
            "excerpt": _excerpt(p.read_text(encoding="utf-8"), limit=400),
        }
        for p in volume_docs
    ]

    pillars_text = ""
    if config.pillars_path.is_file():
        pillars_text = config.pillars_path.read_text(encoding="utf-8")
    global_text = ""
    if global_outline.is_file():
        global_text = global_outline.read_text(encoding="utf-8")

    report = quality_report_summary(project)
    p0_count = report.get("p0", 0) if report.get("available") else None

    volumes = load_volume_plan(project.root)
    deviations = compute_volume_deviations(project.root, volumes, paths=paths)
    ui_profile = ui_profile_from_project_config(config)
    volume_pulse = build_volume_pulse(project.root) if ui_profile.get("volume_pulse_enabled") else None

    return {
        "slug": project.slug,
        "name": config.name,
        "creation_mode": config.creation_mode,
        "quality_profile": config.quality_profile,
        "max_chapter": config.max_chapter,
        "chapters_written": written,
        "coverage_pct": round(written / config.max_chapter * 100, 1)
        if config.max_chapter
        else 0.0,
        "chapters": chapter_rows,
        "volume_summaries": volume_summaries,
        "pillars_excerpt": _excerpt(pillars_text),
        "pillars_path": str(config.pillars_path),
        "global_outline_excerpt": _excerpt(global_text),
        "global_outline_path": str(global_outline),
        "p0_count": p0_count,
        "quality_report_available": bool(report.get("available")),
        "companion_check_cmd": "bash scripts/run-companion-check.sh",
        "advance_batch_hint": (
            f"bash scripts/run-advance-volume.sh 1 {min(10, config.max_chapter)} "
            f"{min(10, config.max_chapter)} 0.30"
        ),
        "notify_per_chapter": settings.notify_per_chapter,
        "advance_volume_summary": settings.advance_volume_summary,
        "locked_volume_count": sum(1 for v in volumes if v.locked),
        "deviation_count": len(deviations),
        "alert_count": sum(1 for d in deviations if d["severity"] == "alert"),
        "deviations": deviations[:30],
        "ui_profile": ui_profile,
        "volume_pulse": volume_pulse,
    }


def creator_chapter_preview(
    project: StudioProject,
    chapter_num: int,
    *,
    body_limit: int = 4000,
    outline_limit: int = 2500,
) -> dict[str, Any]:
    root = project.root if isinstance(project.root, Path) else Path(project.root)
    paths = ProjectPaths.get(root)
    config = ProjectConfig.load(paths)
    if chapter_num < 1 or chapter_num > config.max_chapter:
        raise ValueError(f"chapter {chapter_num} out of range 1–{config.max_chapter}")

    body = paths.read_chapter(chapter_num) or ""
    outline_path = config.chapter_outline_path(chapter_num, paths)
    outline = ""
    if outline_path.is_file():
        outline = outline_path.read_text(encoding="utf-8")

    return {
        "chapter": chapter_num,
        "has_body": bool(body.strip()),
        "has_outline": outline_path.is_file(),
        "word_count": len(re.sub(r"\s+", "", body)),
        "body_preview": body[:body_limit],
        "outline_preview": outline[:outline_limit],
        "body_truncated": len(body) > body_limit,
        "outline_truncated": len(outline) > outline_limit,
    }
