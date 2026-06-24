"""Volume-level pulse summary for advance mode —脉络 without per-chapter noise."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from infra.creator_volume_plan import compute_volume_deviations, load_volume_plan
from infra.paths import ProjectPaths


def _volume_status(deviations: list[dict[str, Any]]) -> str:
    if any(row.get("severity") == "alert" for row in deviations):
        return "alert"
    if deviations:
        return "warn"
    return "ok"


def _volume_headline(
    *,
    written: int,
    total: int,
    deviations: list[dict[str, Any]],
    locked: bool,
) -> str:
    if deviations:
        alert_n = sum(1 for row in deviations if row.get("severity") == "alert")
        if alert_n:
            return f"{alert_n} 条需关注偏离"
        return f"{len(deviations)} 条轻微偏离"
    if written >= total and total > 0:
        return "本卷章位已满"
    if written == 0:
        return "尚未写入正文"
    if locked:
        return f"已写 {written}/{total} 章 · 卷纲已锁定"
    return f"已写 {written}/{total} 章"


def build_volume_pulse(project_root: Path | str) -> dict[str, Any]:
    root = project_root if isinstance(project_root, Path) else Path(project_root)
    paths = ProjectPaths.get(root)
    volumes = load_volume_plan(root)
    all_deviations = compute_volume_deviations(root, volumes, paths=paths)
    dev_by_label: dict[str, list[dict[str, Any]]] = {}
    for row in all_deviations:
        label = str(row.get("volume_label") or row.get("label") or "")
        dev_by_label.setdefault(label, []).append(row)

    volume_rows: list[dict[str, Any]] = []
    for vol in volumes:
        written = 0
        for ch in range(vol.start_chapter, vol.end_chapter + 1):
            if paths.read_chapter(ch):
                written += 1
        total = max(0, vol.end_chapter - vol.start_chapter + 1)
        vol_devs = dev_by_label.get(vol.label, [])
        volume_rows.append(
            {
                "label": vol.label,
                "start_chapter": vol.start_chapter,
                "end_chapter": vol.end_chapter,
                "written": written,
                "total_chapters": total,
                "progress_pct": round(written / total * 100, 1) if total else 0.0,
                "locked": vol.locked,
                "status": _volume_status(vol_devs),
                "deviation_count": len(vol_devs),
                "headline": _volume_headline(
                    written=written,
                    total=total,
                    deviations=vol_devs,
                    locked=vol.locked,
                ),
            },
        )

    docs_dir = root / "docs"
    latest_summary = None
    if docs_dir.is_dir():
        summaries = sorted(docs_dir.glob("volume-summary-ch*.md"), key=lambda p: p.name, reverse=True)
        if summaries:
            text = summaries[0].read_text(encoding="utf-8")
            latest_summary = {
                "name": summaries[0].name,
                "excerpt": text[:400].strip() + ("…" if len(text) > 400 else ""),
            }

    alert_count = sum(1 for row in volume_rows if row["status"] == "alert")
    warn_count = sum(1 for row in volume_rows if row["status"] == "warn")
    return {
        "volume_count": len(volume_rows),
        "alert_count": alert_count,
        "warn_count": warn_count,
        "overall_status": "alert" if alert_count else ("warn" if warn_count else "ok"),
        "volumes": volume_rows,
        "latest_summary": latest_summary,
    }
