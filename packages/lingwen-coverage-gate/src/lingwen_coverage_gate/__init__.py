"""lingwen-coverage-gate — canonical coverage_gate package.

Phase 45 P3-ARCHDEBT: relocated from infra/coverage_gate.py (78 LOC).
TRUE LEAF (0 workspace deps; PyYAML>=6.0 3rd-party only).
"""

from __future__ import annotations

from lingwen_coverage_gate.service import (
    evaluate_module_gate,
    format_module_gate_report,
    load_coverage_policy,
    module_percent,
)

__all__ = ["load_coverage_policy", "module_percent", "evaluate_module_gate", "format_module_gate_report"]