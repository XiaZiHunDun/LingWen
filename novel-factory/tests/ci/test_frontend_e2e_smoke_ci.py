"""Phase 9.48 F37: Playwright opt-in CI workflow contract tests."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
FRONTEND_DIR = REPO_ROOT / "novel-factory" / "dashboard" / "frontend"


class TestDashboardE2ESmokeWorkflow:
    def test_e2e_smoke_workflow_exists(self):
        assert (WORKFLOWS_DIR / "dashboard-e2e-smoke.yml").is_file()

    def test_e2e_smoke_workflow_has_manual_dispatch(self):
        data = yaml.safe_load(
            (WORKFLOWS_DIR / "dashboard-e2e-smoke.yml").read_text(encoding="utf-8")
        )
        triggers = data.get("on") or data.get(True) or {}
        assert "workflow_dispatch" in triggers

    def test_e2e_smoke_workflow_not_on_push(self):
        data = yaml.safe_load(
            (WORKFLOWS_DIR / "dashboard-e2e-smoke.yml").read_text(encoding="utf-8")
        )
        triggers = data.get("on") or data.get(True) or {}
        assert "push" not in triggers

    def test_e2e_smoke_job_uses_playwright_install(self):
        text = (WORKFLOWS_DIR / "dashboard-e2e-smoke.yml").read_text(encoding="utf-8")
        assert "playwright install" in text
        assert "pnpm e2e:smoke" in text


class TestDashboardE2ESmokeSpec:
    def test_app_root_smoke_spec_exists(self):
        spec = FRONTEND_DIR / "tests" / "e2e-smoke" / "app-root.spec.js"
        assert spec.is_file()
        assert "app-root" in spec.read_text(encoding="utf-8")

    def test_live_e2e_specs_exist(self):
        for name in (
            "ripples-audit.spec.js",
            "decisions-resolve.spec.js",
            "creator-workspace.spec.js",
        ):
            spec = FRONTEND_DIR / "tests" / "e2e-smoke" / name
            assert spec.is_file(), name
            text = spec.read_text(encoding="utf-8")
            assert "LINGWEN_E2E_LIVE" in text or "skipUnlessLive" in text

    def test_e2e_seed_module_exists(self):
        seed = REPO_ROOT / "novel-factory" / "infra" / "cross_volume" / "e2e_seed.py"
        assert seed.is_file()

    def test_playwright_config_has_webserver(self):
        text = (FRONTEND_DIR / "playwright.config.js").read_text(encoding="utf-8")
        assert "webServer:" in text
        assert "5173" in text

    def test_package_has_e2e_smoke_script(self):
        pkg = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
        assert pkg["scripts"].get("e2e:smoke") == "playwright test --project=smoke"
        assert "e2e:live" in pkg["scripts"]
        assert "LINGWEN_E2E_LIVE=1" in pkg["scripts"]["e2e:live"]
