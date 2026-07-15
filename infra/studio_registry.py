"""LingWen Studio multi-project registry (Phase 10.04)."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from infra.paths import ProjectPaths
from infra.project_config import ProjectConfig

_CHAPTER_RE = re.compile(r"^ch(\d+)\.md$")
_OUTLINE_RE = re.compile(r"^ch(\d+)_大纲\.md$")
_ACTIVE_STATE = "studio_active.json"


@dataclass(frozen=True)
class StudioProject:
    slug: str
    name: str
    role: str
    root: Path
    location: str  # "root" | "projects"


def factory_root() -> Path:
    return Path(__file__).resolve().parent.parent


def active_state_path() -> Path:
    return factory_root() / "infra" / ".state" / _ACTIVE_STATE


def _load_yaml_project(root: Path) -> dict[str, Any]:
    config_path = root / "config" / "project.yaml"
    if not config_path.is_file():
        return {}
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return data.get("project") or {}


def list_projects() -> list[StudioProject]:
    root = factory_root()
    items: list[StudioProject] = []

    root_raw = _load_yaml_project(root)
    if root_raw:
        items.append(
            StudioProject(
                slug=str(root_raw.get("slug", "default")),
                name=str(root_raw.get("name", "default")),
                role=str(root_raw.get("role", "production")),
                root=root,
                location="root",
            ),
        )

    projects_dir = root / "projects"
    if projects_dir.is_dir():
        for child in sorted(projects_dir.iterdir()):
            if not child.is_dir():
                continue
            raw = _load_yaml_project(child)
            if not raw:
                continue
            items.append(
                StudioProject(
                    slug=str(raw.get("slug", child.name)),
                    name=str(raw.get("name", child.name)),
                    role=str(raw.get("role", "production")),
                    root=child,
                    location="projects",
                ),
            )
    return items


def get_project_by_slug(slug: str) -> StudioProject | None:
    for project in list_projects():
        if project.slug == slug:
            return project
    return None


def read_active_slug() -> str | None:
    state = active_state_path()
    if state.is_file():
        data = json.loads(state.read_text(encoding="utf-8"))
        slug = data.get("slug")
        if slug and get_project_by_slug(str(slug)):
            return str(slug)

    env = os.environ.get("LINGWEN_PROJECT_ROOT", "").strip()
    if env:
        env_path = Path(env).resolve()
        for project in list_projects():
            if project.root.resolve() == env_path:
                return project.slug

    projects = list_projects()
    return projects[0].slug if projects else None


def activate_project(slug: str) -> StudioProject:
    project = get_project_by_slug(slug)
    if project is None:
        raise ValueError(f"unknown project slug: {slug!r}")

    state = active_state_path()
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(
        json.dumps({"slug": slug, "root": str(project.root)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.environ["LINGWEN_PROJECT_ROOT"] = str(project.root)
    ProjectPaths.reset()
    ProjectPaths.get(project.root)
    return project


def active_project() -> StudioProject | None:
    slug = read_active_slug()
    if slug is None:
        return None
    return get_project_by_slug(slug)


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
    from infra.agent_system.chapter_production_batch import resolve_cost_per_chapter_usd

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
    from infra.agent_system.chapter_memory_hook import default_studio_memory_rag_mode

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


def quality_report_summary(project: StudioProject) -> dict[str, Any]:
    """Parsed docs/full-check-report.md for Studio dashboard (Phase 10.07)."""
    from infra.full_check_report import load_report_summary

    return load_report_summary(project.root)


def prose_diff_summary(project: StudioProject) -> dict[str, Any]:
    """Prose snapshot diff vs current full-check report (v12 Dashboard)."""
    from infra.full_check_report import load_report_summary
    from infra.prose_snapshot import (
        build_snapshot,
        diff_snapshots,
        load_snapshot,
        snapshot_path_for,
    )

    snap_path = snapshot_path_for(project.root)
    baseline = load_snapshot(project.root)
    slug = project.slug

    if baseline is None:
        return {
            "slug": slug,
            "available": False,
            "reason": "no_baseline",
            "snapshot_path": str(snap_path),
            "save_command": f"bash scripts/run-prose-diff.sh {slug} --save",
        }

    report = load_report_summary(project.root)
    if not report.get("available"):
        return {
            "slug": slug,
            "available": False,
            "reason": "no_report",
            "snapshot_path": str(snap_path),
            "before_captured_at": baseline.get("captured_at"),
            "save_command": f"bash scripts/generate-full-check-report.sh {slug}",
        }

    current = build_snapshot(slug, report)
    diff = diff_snapshots(baseline, current)
    return {
        "slug": slug,
        "available": True,
        "snapshot_path": str(snap_path),
        "report_path": report.get("path"),
        "before_captured_at": diff.get("before_captured_at"),
        "after_captured_at": diff.get("after_captured_at"),
        "total_delta": diff.get("total_delta") or {},
        "chapters": diff.get("chapters") or [],
        "improved_count": len(diff.get("improved") or []),
        "regressed_count": len(diff.get("regressed") or []),
        "has_regression": bool(diff.get("has_regression")),
        "net_prose_p1_delta": int(diff.get("net_prose_p1_delta") or 0),
    }


def prose_judge_summary(project: StudioProject) -> dict[str, Any]:
    """Prose rubric v2 judge report for Studio dashboard (Phase 12.03)."""
    from infra.full_check_report import load_report_summary
    from infra.prose_judge import (
        load_judge_report,
        report_path_for,
        summarize_judge_report,
    )

    path = report_path_for(project.root)
    judge = load_judge_report(project.root)
    slug = project.slug

    if judge is None:
        return {
            "slug": slug,
            "available": False,
            "reason": "no_report",
            "report_path": str(path),
            "generate_command": f"bash scripts/run-prose-judge.sh {slug}",
        }

    full_check = load_report_summary(project.root)
    summary = summarize_judge_report(judge, full_check if full_check.get("available") else None)
    summary["report_path"] = str(path)
    summary["generate_command"] = f"bash scripts/run-prose-judge.sh {slug} --llm"
    return summary
