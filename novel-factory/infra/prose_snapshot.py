"""Prose revision snapshots and diff (Phase 11.05)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infra.prose_calibration import build_prose_heatmap, is_prose_issue, load_prose_config

SNAPSHOT_VERSION = 1
SNAPSHOT_FILENAME = "prose-snapshot.json"


def snapshot_path_for(project_root: Path) -> Path:
    return project_root / "docs" / SNAPSHOT_FILENAME


def _prose_issue_types_for_chapter(
    issues: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> list[str]:
    cfg = config or load_prose_config()
    seen: list[str] = []
    for issue in issues:
        itype = str(issue.get("issue_type") or "").strip()
        if itype and is_prose_issue(itype, cfg) and itype not in seen:
            seen.append(itype)
    return seen


def build_snapshot(slug: str, report: dict[str, Any]) -> dict[str, Any]:
    """Build a comparable prose metrics snapshot from a parsed full-check report."""
    cfg = load_prose_config()
    heatmap = build_prose_heatmap(report.get("chapters") or [], cfg)
    chapters: list[dict[str, Any]] = []

    for ch in report.get("chapters") or []:
        chapter_num = int(ch.get("chapter") or 0)
        issues = ch.get("issues") or []
        prose_issues = [i for i in issues if is_prose_issue(str(i.get("issue_type", "")), cfg)]
        chapters.append(
            {
                "chapter": chapter_num,
                "issue_count": len(issues),
                "prose_p1": sum(1 for i in prose_issues if i.get("severity") == "P1"),
                "prose_total": len(prose_issues),
                "prose_issue_types": _prose_issue_types_for_chapter(issues, cfg),
            },
        )

    return {
        "version": SNAPSHOT_VERSION,
        "slug": slug,
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "full-check-report",
        "totals": {
            "p0": int(report.get("p0") or 0),
            "p1": int(report.get("p1") or 0),
            "p2": int(report.get("p2") or 0),
            "p3": int(report.get("p3") or 0),
            "total": int(report.get("total") or 0),
            "prose_p1": heatmap["total_prose_p1"],
            "prose_total": heatmap["total_prose_issues"],
        },
        "chapters": chapters,
    }


def save_snapshot(project_root: Path, snapshot: dict[str, Any]) -> Path:
    path = snapshot_path_for(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_snapshot(project_root: Path) -> dict[str, Any] | None:
    path = snapshot_path_for(project_root)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _chapter_map(snapshot: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(c["chapter"]): c for c in snapshot.get("chapters") or []}


def diff_snapshots(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Compare two prose snapshots; lower prose counts = improvement."""
    before_totals = before.get("totals") or {}
    after_totals = after.get("totals") or {}
    total_delta: dict[str, int] = {}
    for key in ("p0", "p1", "total", "prose_p1", "prose_total"):
        total_delta[key] = int(after_totals.get(key) or 0) - int(before_totals.get(key) or 0)

    before_ch = _chapter_map(before)
    after_ch = _chapter_map(after)
    chapter_rows: list[dict[str, Any]] = []
    improved: list[dict[str, Any]] = []
    regressed: list[dict[str, Any]] = []

    for chapter in sorted(set(before_ch) | set(after_ch)):
        b = before_ch.get(chapter, {})
        a = after_ch.get(chapter, {})
        delta_p1 = int(a.get("prose_p1") or 0) - int(b.get("prose_p1") or 0)
        delta_total = int(a.get("prose_total") or 0) - int(b.get("prose_total") or 0)
        row = {
            "chapter": chapter,
            "before_prose_p1": int(b.get("prose_p1") or 0),
            "after_prose_p1": int(a.get("prose_p1") or 0),
            "delta_prose_p1": delta_p1,
            "before_prose_total": int(b.get("prose_total") or 0),
            "after_prose_total": int(a.get("prose_total") or 0),
            "delta_prose_total": delta_total,
        }
        chapter_rows.append(row)
        if delta_p1 < 0 or (delta_p1 == 0 and delta_total < 0):
            improved.append(row)
        elif delta_p1 > 0 or (delta_p1 == 0 and delta_total > 0):
            regressed.append(row)

    has_regression = (
        total_delta.get("prose_p1", 0) > 0
        or total_delta.get("prose_total", 0) > 0
        or total_delta.get("p0", 0) > 0
        or bool(regressed)
    )

    return {
        "slug": after.get("slug") or before.get("slug"),
        "before_captured_at": before.get("captured_at"),
        "after_captured_at": after.get("captured_at"),
        "total_delta": total_delta,
        "chapters": chapter_rows,
        "improved": improved,
        "regressed": regressed,
        "has_regression": has_regression,
        "net_prose_p1_delta": total_delta.get("prose_p1", 0),
    }


def format_diff_report(diff: dict[str, Any]) -> str:
    slug = diff.get("slug") or "?"
    lines = [
        f"=== Prose revision diff: {slug} ===",
        f"baseline: {diff.get('before_captured_at') or '(unknown)'}",
        f"current:  {diff.get('after_captured_at') or '(unknown)'}",
        "",
    ]
    td = diff.get("total_delta") or {}
    for key in ("prose_p1", "prose_total", "total", "p0", "p1"):
        if key not in td:
            continue
        delta = td[key]
        sign = "+" if delta > 0 else ""
        mark = ""
        if key in ("prose_p1", "prose_total", "total", "p0") and delta < 0:
            mark = " ✓"
        elif key in ("prose_p1", "prose_total", "total", "p0") and delta > 0:
            mark = " ⚠"
        lines.append(f"  {key}: {sign}{delta}{mark}")

    improved = diff.get("improved") or []
    regressed = diff.get("regressed") or []
    lines.append("")
    if improved:
        lines.append("chapters improved:")
        for row in improved:
            lines.append(
                f"  ch{row['chapter']:02d}: prose_p1 "
                f"{row['before_prose_p1']}→{row['after_prose_p1']} "
                f"({row['delta_prose_p1']:+d})",
            )
    else:
        lines.append("chapters improved: (none)")

    lines.append("")
    if regressed:
        lines.append("chapters regressed:")
        for row in regressed:
            lines.append(
                f"  ch{row['chapter']:02d}: prose_p1 "
                f"{row['before_prose_p1']}→{row['after_prose_p1']} "
                f"({row['delta_prose_p1']:+d})",
            )
    else:
        lines.append("chapters regressed: (none)")

    lines.append("")
    if diff.get("has_regression"):
        lines.append("=== REGRESSION (prose metrics worsened) ===")
    else:
        lines.append("=== NO REGRESSION ===")
    return "\n".join(lines)
