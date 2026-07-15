"""Prose calibration and heatmap helpers (Phase 11.23)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_FACTORY_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_CONFIG = _FACTORY_ROOT / "config" / "prose_calibration.yaml"


@lru_cache(maxsize=1)
def load_prose_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or _DEFAULT_CONFIG
    if not cfg_path.is_file():
        return {
            "primary_revision_gate": {"max_p0": 0, "max_prose_p1": 15, "max_total": 24},
            "golden_baselines": {},
            "prose_issue_types": [],
            "prose_issue_substrings": [],
        }
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}


def is_prose_issue(issue_type: str, config: dict[str, Any] | None = None) -> bool:
    cfg = config or load_prose_config()
    normalized = (issue_type or "").strip()
    if not normalized:
        return False
    exact: set[str] = set(cfg.get("prose_issue_types") or [])
    if normalized in exact:
        return True
    lowered = normalized.lower()
    for sub in cfg.get("prose_issue_substrings") or []:
        if sub.lower() in lowered or sub in normalized:
            return True
    return False


def build_prose_heatmap(chapters: list[dict[str, Any]], config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build per-chapter prose issue counts for Studio dashboard."""
    cfg = config or load_prose_config()
    rows: list[dict[str, Any]] = []
    max_prose = 0

    for ch in chapters:
        chapter_num = int(ch.get("chapter") or 0)
        issues = ch.get("issues") or []
        prose_issues = [
            i for i in issues if is_prose_issue(str(i.get("issue_type", "")), cfg)
        ]
        structural = len(issues) - len(prose_issues)
        prose_count = len(prose_issues)
        max_prose = max(max_prose, prose_count)
        rows.append(
            {
                "chapter": chapter_num,
                "issue_count": len(issues),
                "prose_p1": sum(1 for i in prose_issues if i.get("severity") == "P1"),
                "prose_total": prose_count,
                "structural_total": structural,
                "heat": 0.0,
            },
        )

    for row in rows:
        if max_prose > 0:
            row["heat"] = round(row["prose_total"] / max_prose, 3)
        else:
            row["heat"] = 0.0

    total_prose = sum(r["prose_total"] for r in rows)
    total_prose_p1 = sum(r["prose_p1"] for r in rows)

    return {
        "chapters": rows,
        "max_prose_per_chapter": max_prose,
        "total_prose_issues": total_prose,
        "total_prose_p1": total_prose_p1,
    }


def evaluate_against_baseline(
    slug: str,
    report: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare parsed full-check report to golden baseline for slug."""
    cfg = config or load_prose_config()
    gate = cfg.get("primary_revision_gate") or {}
    baselines: dict[str, Any] = cfg.get("golden_baselines") or {}
    baseline = baselines.get(slug) or {}

    heatmap = build_prose_heatmap(report.get("chapters") or [], cfg)
    p0 = int(report.get("p0") or 0)
    total = int(report.get("total") or 0)
    prose_p1 = heatmap["total_prose_p1"]
    prose_total = heatmap["total_prose_issues"]

    limits = {
        "max_p0": int(baseline.get("max_p0", gate.get("max_p0", 0))),
        "max_prose_p1": int(baseline.get("max_prose_p1", gate.get("max_prose_p1", 15))),
        "max_total": int(baseline.get("max_total", gate.get("max_total", 24))),
    }

    checks = [
        {"name": "p0", "value": p0, "limit": limits["max_p0"], "passed": p0 <= limits["max_p0"]},
        {
            "name": "prose_p1",
            "value": prose_p1,
            "limit": limits["max_prose_p1"],
            "passed": prose_p1 <= limits["max_prose_p1"],
        },
        {
            "name": "total",
            "value": total,
            "limit": limits["max_total"],
            "passed": total <= limits["max_total"],
        },
    ]
    passed = all(c["passed"] for c in checks)

    return {
        "slug": slug,
        "label": baseline.get("label") or slug,
        "dist_ready": bool(baseline.get("dist_ready", False)),
        "passed": passed,
        "p0": p0,
        "total": total,
        "prose_p1": prose_p1,
        "prose_total": prose_total,
        "limits": limits,
        "checks": checks,
        "heatmap": heatmap,
    }


def format_calibration_report(results: list[dict[str, Any]]) -> str:
    lines = ["=== Prose calibration report ===", ""]
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"[{status}] {r['label']} ({r['slug']})")
        lines.append(
            f"  P0={r['p0']} · total={r['total']} · prose_p1={r['prose_p1']} · prose_total={r['prose_total']}",
        )
        for c in r["checks"]:
            mark = "ok" if c["passed"] else "OVER"
            lines.append(f"  - {c['name']}: {c['value']} (limit {c['limit']}) [{mark}]")
        lines.append("")
    all_pass = all(r["passed"] for r in results)
    lines.append("=== ALL PASS ===" if all_pass else "=== CALIBRATION FAILED ===")
    return "\n".join(lines)


def list_primary_revision_slugs(config: dict[str, Any] | None = None) -> list[str]:
    """Slugs with dist_ready in golden_baselines (七样章主修书)."""
    cfg = config or load_prose_config()
    baselines: dict[str, Any] = cfg.get("golden_baselines") or {}
    return sorted(slug for slug, spec in baselines.items() if spec.get("dist_ready"))


def is_primary_revision_slug(slug: str, config: dict[str, Any] | None = None) -> bool:
    return slug in list_primary_revision_slugs(config)


def resolve_llm_post_check(
    slug: str,
    *,
    mode: str | None,
    has_api_key: bool,
    config: dict[str, Any] | None = None,
) -> str:
    """Resolve LLM Golden post-check: run | skip | fail_no_key."""
    _ = config
    normalized = (mode or "").strip().lower()
    primary = is_primary_revision_slug(slug)

    if normalized in ("0", "off", "false", "skip", "no"):
        return "skip"
    if normalized in ("1", "on", "true", "force", "require", "blocking", "block"):
        return "run" if has_api_key else "fail_no_key"
    if normalized == "auto":
        return "run" if has_api_key else "skip"

    # unset: primary revision books block without key
    if primary:
        return "run" if has_api_key else "fail_no_key"
    return "run" if has_api_key else "skip"

