"""Prose snapshot — golden-set versioned point-in-time captures + diff.

Phase 51 P3-ARCHDEBT: relocated verbatim from infra/prose_snapshot.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lingwen_prose_calibration import build_prose_heatmap, is_prose_issue, load_prose_config

SNAPSHOT_VERSION = 1
SNAPSHOT_FILENAME = "prose-snapshot.json"


def snapshot_path_for(project_root: Path) -> Path:
    return project_root / "docs" / SNAPSHOT_FILENAME


def _prose_issue_types_for_chapter(
    issues: list[dict[str, Any]], config: dict[str, Any] | None = None
) -> list[str]:
    cfg = config or load_prose_config()
    return sorted(
        {
            str(i.get("issue_type", "")).strip()
            for i in issues
            if is_prose_issue(str(i.get("issue_type", "")), cfg)
        }
    )


def build_snapshot(slug: str, report: dict[str, Any]) -> dict[str, Any]:
    cfg = load_prose_config()
    issue_map: dict[int, list[dict[str, Any]]] = {}
    for ch in report.get("chapters") or []:
        issue_map[int(ch["chapter"])] = list(ch.get("issues") or [])

    chapters: list[dict[str, Any]] = []
    for chapter_num, issues in sorted(issue_map.items()):
        types = _prose_issue_types_for_chapter(issues, cfg)
        heatmap = build_prose_heatmap(chapter_num, issues, cfg)
        chapters.append(
            {
                "chapter": chapter_num,
                "issue_types": types,
                "issue_count": len(types),
                "vitality_score": float(heatmap.get("vitality_score", 0.0)),
                "p1_issue_types": [
                    str(i.get("issue_type", "")).strip()
                    for i in issues
                    if str(i.get("severity")) == "P1"
                    and is_prose_issue(str(i.get("issue_type", "")), cfg)
                ],
            }
        )

    return {
        "version": SNAPSHOT_VERSION,
        "slug": slug,
        "captured_at": report.get("generated_at"),
        "chapters": chapters,
        "summary": {
            "chapter_count": len(chapters),
            "total_p1_issue_types": sum(len(c["p1_issue_types"]) for c in chapters),
            "avg_vitality_score": round(
                sum(c["vitality_score"] for c in chapters) / len(chapters), 2
            )
            if chapters
            else 0.0,
        },
    }


def save_snapshot(project_root: Path, snapshot: dict[str, Any]) -> Path:
    path = snapshot_path_for(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def load_snapshot(project_root: Path) -> dict[str, Any] | None:
    path = snapshot_path_for(project_root)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _chapter_map(snapshot: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(c["chapter"]): c for c in snapshot.get("chapters") or []}


def diff_snapshots(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_map = _chapter_map(before)
    after_map = _chapter_map(after)
    chapter_nums = sorted(set(before_map) | set(after_map))

    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    improved: list[dict[str, Any]] = []
    regressed: list[dict[str, Any]] = []

    for ch in chapter_nums:
        b = before_map.get(ch)
        a = after_map.get(ch)
        if b is None and a is not None:
            added.append(
                {
                    "chapter": ch,
                    "issue_types": a.get("issue_types") or [],
                    "p1_issue_types": a.get("p1_issue_types") or [],
                }
            )
            continue
        if a is None and b is not None:
            removed.append(
                {
                    "chapter": ch,
                    "issue_types": b.get("issue_types") or [],
                    "p1_issue_types": b.get("p1_issue_types") or [],
                }
            )
            continue
        if b is None or a is None:
            continue

        b_types = set(b.get("issue_types") or [])
        a_types = set(a.get("issue_types") or [])
        new_types = sorted(a_types - b_types)
        fixed_types = sorted(b_types - a_types)
        v_before = float(b.get("vitality_score", 0.0))
        v_after = float(a.get("vitality_score", 0.0))
        delta = round(v_after - v_before, 2)

        if new_types or fixed_types or delta != 0.0:
            row = {
                "chapter": ch,
                "new_issue_types": new_types,
                "fixed_issue_types": fixed_types,
                "vitality_before": v_before,
                "vitality_after": v_after,
                "vitality_delta": delta,
            }
            if delta > 0:
                improved.append(row)
            elif delta < 0:
                regressed.append(row)

    b_total = sum(len(c.get("p1_issue_types") or []) for c in before.get("chapters") or [])
    a_total = sum(len(c.get("p1_issue_types") or []) for c in after.get("chapters") or [])
    return {
        "before_slug": before.get("slug"),
        "after_slug": after.get("slug"),
        "added": added,
        "removed": removed,
        "improved": improved,
        "regressed": regressed,
        "totals": {
            "p1_issue_types_before": b_total,
            "p1_issue_types_after": a_total,
            "p1_delta": a_total - b_total,
            "added_chapters": len(added),
            "removed_chapters": len(removed),
            "improved_chapters": len(improved),
            "regressed_chapters": len(regressed),
        },
    }


def format_diff_report(diff: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Prose Snapshot Diff",
        "",
        f"> **Before**: `{diff.get('before_slug')}`",
        f"> **After**: `{diff.get('after_slug')}`",
        "",
        "## Totals",
        "",
        "| Metric | Before | After | Delta |",
        "|--------|--------|-------|-------|",
    ]
    totals = diff.get("totals") or {}
    lines.append(
        f"| P1 issue types | {totals.get('p1_issue_types_before', 0)} "
        f"| {totals.get('p1_issue_types_after', 0)} "
        f"| {totals.get('p1_delta', 0):+d} |"
    )
    lines.append(
        f"| Added / Removed chapters | — | — "
        f"| +{totals.get('added_chapters', 0)} / -{totals.get('removed_chapters', 0)} |"
    )
    lines.append(
        f"| Improved / Regressed chapters | — | — "
        f"| +{totals.get('improved_chapters', 0)} / -{totals.get('regressed_chapters', 0)} |"
    )
    lines.append("")

    if diff.get("added"):
        lines.append("## Added Chapters")
        lines.append("")
        for row in diff["added"]:
            lines.append(f"- **ch{row['chapter']:03d}** — {', '.join(row['issue_types']) or '(no prose issues)'}")
        lines.append("")

    if diff.get("removed"):
        lines.append("## Removed Chapters")
        lines.append("")
        for row in diff["removed"]:
            lines.append(f"- **ch{row['chapter']:03d}** — {', '.join(row['issue_types']) or '(no prose issues)'}")
        lines.append("")

    if diff.get("improved"):
        lines.append("## Improved Chapters (vitality ↑)")
        lines.append("")
        for row in diff["improved"]:
            lines.append(
                f"- **ch{row['chapter']:03d}** vitality "
                f"{row['vitality_before']} → {row['vitality_after']} "
                f"(Δ {row['vitality_delta']:+.2f}); "
                f"new: {', '.join(row['new_issue_types']) or '—'}; "
                f"fixed: {', '.join(row['fixed_issue_types']) or '—'}"
            )
        lines.append("")

    if diff.get("regressed"):
        lines.append("## Regressed Chapters (vitality ↓)")
        lines.append("")
        for row in diff["regressed"]:
            lines.append(
                f"- **ch{row['chapter']:03d}** vitality "
                f"{row['vitality_before']} → {row['vitality_after']} "
                f"(Δ {row['vitality_delta']:+.2f}); "
                f"new: {', '.join(row['new_issue_types']) or '—'}; "
                f"fixed: {', '.join(row['fixed_issue_types']) or '—'}"
            )
        lines.append("")

    if not (diff.get("added") or diff.get("removed") or diff.get("improved") or diff.get("regressed")):
        lines.append("**No chapter-level prose changes between snapshots.**")
        lines.append("")

    return "\n".join(lines)
