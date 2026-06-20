"""Phase 11.11: coverage gate contract + module policy tests."""
from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"


class TestCoverageModulesPolicy:
    def test_policy_file_exists(self):
        path = NOVEL_FACTORY / "config" / "coverage_modules.yaml"
        assert path.is_file()
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["global_min_percent"] == 40
        assert data["modules"]["infra"]["min_percent"] == 40
        assert data["modules"]["dashboard"]["min_percent"] == 40
        assert data["modules"]["tools"]["min_percent"] == 30

    def test_pyproject_coverage_omit_legacy_tools(self):
        text = (NOVEL_FACTORY / "pyproject.toml").read_text(encoding="utf-8")
        assert "[tool.coverage.run]" in text
        assert "tools/quick_check.py" in text
        assert "tools/llm_quality_analyzer.py" in text

    def test_ci_cov_fail_under_40(self):
        wf = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        assert "--cov-fail-under=40" in wf
        assert "verify-coverage-modules.sh" in wf

    def test_ci_cov_config_pyproject(self):
        wf = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        assert "--cov-config=pyproject.toml" in wf

    def test_verify_script_exists(self):
        script = NOVEL_FACTORY / "scripts" / "verify-coverage-modules.sh"
        assert script.is_file()
        assert "evaluate_module_gate" in script.read_text(encoding="utf-8")


class TestCoverageGateModule:
    def test_evaluate_module_gate_passes_on_current_data(self):
        from coverage import Coverage

        from infra.coverage_gate import evaluate_module_gate

        cov_file = NOVEL_FACTORY / ".coverage"
        if not cov_file.is_file():
            import pytest

            pytest.skip(".coverage artifact missing — run full pytest --cov locally")

        cov = Coverage(data_file=str(cov_file))
        cov.load()
        report = evaluate_module_gate(cov)
        assert report["modules"]
        assert report["passed"] is True
