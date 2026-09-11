"""Coverage module gate helpers (Phase 11.11).

Phase 45 P3-ARCHDEBT: relocated from infra/coverage_gate.py (78 LOC).
TRUE LEAF (0 workspace deps; PyYAML>=6.0 3rd-party only).

Architecture note: _FACTORY_ROOT resolves via parents[4] from the new
package location (packages/lingwen-coverage-gate/src/lingwen_coverage_gate/service.py)
to the repo root. Same pattern as Phase 40a C1.5 + Phase 44.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Phase 45: parents[4] from new location → repo root
# (was parents[1] from infra/coverage_gate.py)
_FACTORY_ROOT = Path(__file__).resolve().parents[4]
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
            f"[{mark}] {row['module']}: {row['actual_percent']}% (min {row['min_percent']}%)",
        )
    lines.append("")
    lines.append("=== ALL PASS ===" if report.get("passed") else "=== MODULE GATE FAILED ===")
    return "\n".join(lines)


__all__ = ["load_coverage_policy", "module_percent", "evaluate_module_gate", "format_module_gate_report"]