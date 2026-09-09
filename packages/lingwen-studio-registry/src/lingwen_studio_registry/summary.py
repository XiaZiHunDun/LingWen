"""Project, quality, preflight, and batch summaries."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lingwen_paths import ProjectPaths
from lingwen_project_config import ProjectConfig

from lingwen_studio_registry.discovery import factory_root
from lingwen_studio_registry.models import (
    _CHAPTER_RE,
    _OUTLINE_RE,
    StudioProject,
)


def _chapter_nums(chapters_dir: Path) -> list[int]:
    if not chapters_dir.is_dir():
        return []
    nums: list[int] = []
    for path in chapters_dir.glob("ch*.md"):
        match = _CHAPTER_RE.match(path.name)
        if match:
            nums.append(int(match.group(1)))
    return sorted(nums)


def _outline_nums(chapters_dir: Path) -> list[int]:
    if not chapters_dir.is_dir():
        return []
    nums: list[int] = []
    for path in chapters_dir.glob("ch*_大纲.md"):
        match = _OUTLINE_RE.match(path.name)
        if match:
            nums.append(int(match.group(1)))
    return sorted(nums)


def pilot_records_dir_for(project: StudioProject) -> Path:
    candidate = project.root / ".state" / "pilot_records"
    if candidate.is_dir():
        return candidate
    legacy = factory_root() / "infra" / ".state" / "pilot_records"
    return legacy


def project_summary(project: StudioProject) -> dict[str, Any]:
    config = ProjectConfig.load(ProjectPaths.get(project.root))
    chapters_dir = project.root / "03_内容仓库" / "04_正文"
    chapter_nums = _chapter_nums(chapters_dir)
    outline_nums = _outline_nums(chapters_dir)
    golden_manifest = project.root / "golden-set" / "manifest.json"
    golden_chapters: list[int] = []
    if golden_manifest.is_file():
        data = json.loads(golden_manifest.read_text(encoding="utf-8"))
        golden_chapters = [int(c["num"]) for c in data.get("chapters", []) if "num" in c]

    records_dir = pilot_records_dir_for(project)
    record_count = len(list(records_dir.glob("*.json"))) if records_dir.is_dir() else 0

    return {
        "slug": project.slug,
        "name": project.name,
        "role": project.role,
        "root": str(project.root),
        "location": project.location,
        "max_chapter": config.max_chapter,
        "genre": config.genre,
        "chapter_count": len(chapter_nums),
        "latest_chapter": chapter_nums[-1] if chapter_nums else 0,
        "outline_count": len(outline_nums),
        "golden_chapters": golden_chapters,
        "has_golden_set": golden_manifest.is_file(),
        "pilot_records_dir": str(records_dir),
        "pilot_record_count": record_count,
        "pillars_ok": config.pillars_path.is_file(),
        "pillars_path": str(config.pillars_path),
        "creation_mode": config.creation_mode,
        "quality_profile": config.quality_profile,
    }


def quality_summary(project: StudioProject) -> dict[str, Any]:
    config = ProjectConfig.load(ProjectPaths.get(project.root))
    chapters_dir = project.root / "03_内容仓库" / "04_正文"
    chapter_nums = set(_chapter_nums(chapters_dir))
    outline_nums = set(_outline_nums(chapters_dir))

    missing_outlines: list[int] = []
    if config.require_chapter_outline:
        for num in range(1, config.max_chapter + 1):
            if num not in outline_nums and num not in chapter_nums:
                continue
            if num not in outline_nums:
                missing_outlines.append(num)

    missing_bodies: list[int] = []
    for num in sorted(outline_nums):
        if num not in chapter_nums and num <= config.max_chapter:
            missing_bodies.append(num)

    golden_manifest = project.root / "golden-set" / "manifest.json"
    golden_status = "none"
    if golden_manifest.is_file():
        golden_status = "ready"

    coverage_pct = 0.0
    if config.max_chapter > 0:
        coverage_pct = round(len(chapter_nums) / config.max_chapter * 100, 1)

    return {
        "slug": project.slug,
        "pillars_ok": config.pillars_path.is_file(),
        "pillars_path": str(config.pillars_path),
        "require_chapter_outline": config.require_chapter_outline,
        "max_chapter": config.max_chapter,
        "chapters_written": len(chapter_nums),
        "outlines_present": len(outline_nums),
        "coverage_pct": coverage_pct,
        "missing_outlines": missing_outlines[:20],
        "missing_bodies": missing_bodies[:20],
        "golden_set_status": golden_status,
        "golden_regression_cmd": f"./scripts/run-golden-set-check.sh {project.slug}",
    }


def production_preflight(
    project: StudioProject,
    *,
    start_chapter: int,
    end_chapter: int,
    mode: str = "canon",
) -> dict[str, Any]:
    if start_chapter < 1 or end_chapter < start_chapter:
        raise ValueError("invalid chapter range")

    paths = ProjectPaths.get(project.root)
    config = ProjectConfig.load(paths)
    rows: list[dict[str, Any]] = []
    all_ok = True

    for chapter_num in range(start_chapter, end_chapter + 1):
        ok, message = config.validate_production(chapter_num, mode=mode, paths=paths)
        if not ok:
            all_ok = False
        rows.append({"chapter": chapter_num, "ok": ok, "message": message})

    return {
        "slug": project.slug,
        "mode": mode,
        "start_chapter": start_chapter,
        "end_chapter": end_chapter,
        "all_ok": all_ok,
        "chapters": rows,
    }


def find_calibration_batch(project: StudioProject) -> Path | None:
    """Latest batch summary JSON under this project's pilot_records only."""
    records = project.root / ".state" / "pilot_records"
    if not records.is_dir():
        return None
    batches = sorted(
        records.glob("batch-*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return batches[0] if batches else None


def suggest_batch_budget_usd(
    *,
    num_chapters: int,
    cost_per_chapter_usd: float,
    margin: float = 1.15,
) -> float:
    """Recommend batch budget with headroom (default +15%)."""
    if num_chapters < 1:
        raise ValueError("num_chapters must be >= 1")
    return round(cost_per_chapter_usd * num_chapters * margin, 2)


def batch_command(
    project: StudioProject,
    *,
    start_chapter: int,
    end_chapter: int,
    budget_usd: float | None = None,
    calibrate_json: str = "",
) -> str:
    from lingwen_core.agents.chapter_production_batch import resolve_cost_per_chapter_usd

    max_chapters = end_chapter - start_chapter + 1
    cal_path = Path(calibrate_json) if calibrate_json else find_calibration_batch(project)
    calibrate_from = cal_path if cal_path and cal_path.is_file() else None
    cost_per_ch, _ = resolve_cost_per_chapter_usd(calibrate_from=calibrate_from)
    if budget_usd is None:
        budget_usd = suggest_batch_budget_usd(
            num_chapters=max_chapters,
            cost_per_chapter_usd=cost_per_ch,
        )
    lines = [
        f'export LINGWEN_PROJECT_ROOT="{project.root}"',
        "export LINGWEN_PRODUCTION_MODE=canon",
        "export LINGWEN_REAL_LLM=1",
        "export LINGWEN_EMIT_CHAPTER=1",
    ]
    from lingwen_core.agents.chapter_memory_hook import default_studio_memory_rag_mode

    mem_mode = default_studio_memory_rag_mode()
    lines.append(f"export LINGWEN_MEMORY_RAG={mem_mode}")
    calibrate_arg = ""
    if calibrate_from is not None:
        calibrate_arg = f' "{calibrate_from}"'
    lines.append(
        f"./scripts/run-project-batch.sh {start_chapter} {end_chapter} "
        f"{max_chapters} {budget_usd:.2f}{calibrate_arg}",
    )
    return "\n".join(lines)


