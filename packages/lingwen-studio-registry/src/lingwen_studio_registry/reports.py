"""Dashboard report summaries backed by existing infra report modules."""
from __future__ import annotations

from typing import Any

from lingwen_studio_registry.models import StudioProject


def quality_report_summary(project: StudioProject) -> dict[str, Any]:
    """Parsed docs/full-check-report.md for Studio dashboard (Phase 10.07)."""
    from lingwen_full_check_report import load_report_summary

    return load_report_summary(project.root)


def prose_diff_summary(project: StudioProject) -> dict[str, Any]:
    """Prose snapshot diff vs current full-check report (v12 Dashboard)."""
    from lingwen_full_check_report import load_report_summary
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
    from lingwen_full_check_report import load_report_summary
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
