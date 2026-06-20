"""Tests for infra.coverage_gate (Phase 11.11)."""
from __future__ import annotations

from pathlib import Path

from infra.coverage_gate import (
    evaluate_module_gate,
    format_module_gate_report,
    load_coverage_policy,
    module_percent,
)


class TestCoverageGateHelpers:
    def test_load_coverage_policy(self) -> None:
        policy = load_coverage_policy()
        assert policy["global_min_percent"] == 40
        assert "infra" in policy["modules"]

    def test_format_module_gate_report(self) -> None:
        text = format_module_gate_report(
            {
                "passed": True,
                "modules": [
                    {"module": "infra", "actual_percent": 65.0, "min_percent": 40, "passed": True},
                ],
            },
        )
        assert "infra" in text
        assert "ALL PASS" in text

    def test_module_percent_on_current_data(self) -> None:
        from coverage import Coverage

        cov_file = Path(".coverage")
        if not cov_file.is_file():
            import pytest

            pytest.skip(".coverage missing")
        cov = Coverage(data_file=str(cov_file))
        cov.load()
        pct = module_percent(cov, "/infra/")
        assert pct >= 40.0

    def test_evaluate_module_gate_structure(self) -> None:
        from coverage import Coverage

        cov_file = Path(".coverage")
        if not cov_file.is_file():
            import pytest

            pytest.skip(".coverage missing")
        cov = Coverage(data_file=str(cov_file))
        cov.load()
        report = evaluate_module_gate(cov)
        assert "modules" in report
        assert isinstance(report["passed"], bool)
