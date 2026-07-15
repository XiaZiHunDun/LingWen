"""Coverage module gate helpers (Phase 11.11)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_FACTORY_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_POLICY = _FACTORY_ROOT / "config" / "coverage_modules.yaml"


def load_coverage_policy(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or _DEFAULT_POLICY
    if not cfg_path.is_file():
        return {"global_min_percent": 40, "modules": {}}
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}


def module_percent(coverage: Any, include_prefix: str) -> float:
    """Return line coverage % for files whose path contains include_prefix."""
    total = covered = 0
    for filename in coverage.get_data().measured_files():
        norm = str(filename).replace("\\", "/")
        if include_prefix not in norm:
            continue
        try:
            _, statements, _, missing, _ = coverage.analysis2(filename)
        except Exception:
            continue
        total += len(statements)
        covered += len(statements) - len(missing)
    if total == 0:
        return 100.0
    return round(100.0 * covered / total, 2)


def evaluate_module_gate(
    coverage: Any,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare .coverage data against config/coverage_modules.yaml floors."""
    cfg = policy or load_coverage_policy()
    modules_cfg: dict[str, Any] = cfg.get("modules") or {}
    results: list[dict[str, Any]] = []

    for name, spec in modules_cfg.items():
        min_pct = float(spec.get("min_percent", 0))
        prefix = f"/{name}/"
        actual = module_percent(coverage, prefix)
        results.append(
            {
                "module": name,
                "min_percent": min_pct,
                "actual_percent": actual,
                "passed": actual >= min_pct,
            },
        )

    all_pass = all(r["passed"] for r in results)
    return {
        "global_min_percent": float(cfg.get("global_min_percent", 40)),
        "modules": results,
        "passed": all_pass,
    }


def format_module_gate_report(report: dict[str, Any]) -> str:
    lines = ["=== Coverage module gate ===", ""]
    for row in report.get("modules") or []:
        mark = "PASS" if row["passed"] else "FAIL"
        lines.append(
            f"[{mark}] {row['module']}: {row['actual_percent']}% "
            f"(min {row['min_percent']}%)",
        )
    lines.append("")
    lines.append("=== ALL PASS ===" if report.get("passed") else "=== MODULE GATE FAILED ===")
    return "\n".join(lines)
