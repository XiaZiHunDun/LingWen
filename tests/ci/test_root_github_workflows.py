"""Phase 9.37 F22: repo-root GitHub Actions workflows (pytest CI gate)."""
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


class TestRootGithubWorkflows:
    def test_root_test_workflow_exists(self):
        assert (WORKFLOWS_DIR / "test.yml").is_file()

    def test_root_test_workflow_valid_yaml(self):
        data = yaml.safe_load((WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8"))
        assert data["name"] == "test"
        # YAML 1.1: bare `on` key parses as boolean True
        triggers = data.get("on") or data.get(True)
        assert triggers is not None
        assert "push" in triggers

    def test_root_test_workflow_no_novel_factory_prefix(self):
        text = (WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8")
        # After migration, workflows should not reference novel-factory/ prefix
        assert "novel-factory" not in text
        assert "pytest tests/" in text

    def test_root_test_workflow_has_pytest_timeout(self):
        text = (WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8")
        assert "--timeout=120" in text

    def test_root_dashboard_frontend_ci_paths_include_frontend(self):
        text = (WORKFLOWS_DIR / "dashboard-frontend-ci.yml").read_text(encoding="utf-8")
        assert "dashboard/frontend/**" in text
