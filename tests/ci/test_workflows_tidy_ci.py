"""Phase 12.08: CI workflow tidy — no duplicate e2e-live, coverage pages manual only."""
from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"


class TestWorkflowsTidy1208:
    def test_no_duplicate_dashboard_e2e_live_workflow(self):
        assert not (WORKFLOWS / "dashboard-e2e-live.yml").exists()

    def test_novel_factory_github_workflows_deprecated(self):
        # After migration, novel-factory/ no longer exists; legacy workflows path should be absent.
        legacy = REPO_ROOT / "novel-factory" / ".github" / "workflows"
        assert not legacy.exists(), "legacy novel-factory/.github/workflows should not exist after migration"

    def test_coverage_pages_manual_dispatch_only(self):
        data = yaml.safe_load(
            (WORKFLOWS / "dashboard-frontend-coverage-pages.yml").read_text(encoding="utf-8"),
        )
        triggers = data.get("on") or data.get(True) or {}
        assert "workflow_dispatch" in triggers
        assert "push" not in triggers

    def test_primary_test_has_e2e_live_blocking_job(self):
        text = (WORKFLOWS / "dashboard-frontend-ci.yml").read_text(encoding="utf-8")
        assert "e2e-live:" in text
        assert "pnpm e2e:live" in text
        assert "Upload Playwright trace on failure" in text
