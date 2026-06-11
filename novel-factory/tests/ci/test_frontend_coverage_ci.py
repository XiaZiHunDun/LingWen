"""Phase 9.53 F42: Vitest coverage pipeline contract tests (thresholds 80%)."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = REPO_ROOT / "novel-factory" / "dashboard" / "frontend"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


class TestFrontendCoveragePackage:
    def test_package_has_coverage_devdep(self):
        pkg = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
        assert "@vitest/coverage-v8" in pkg.get("devDependencies", {})

    def test_package_has_test_coverage_scripts(self):
        pkg = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
        scripts = pkg.get("scripts", {})
        assert scripts.get("test") == "vitest run"
        assert scripts.get("test:coverage") == "vitest run --coverage"


class TestFrontendCoverageVitestConfig:
    def test_vitest_config_v8_provider_and_thresholds(self):
        text = (FRONTEND_DIR / "vitest.config.js").read_text(encoding="utf-8")
        assert "provider: 'v8'" in text
        assert "reporter: ['text', 'lcov', 'html']" in text
        assert "thresholds:" in text
        assert "lines: 80" in text
        assert "statements: 78" in text
        assert "functions: 76" in text
        assert "branches: 64" in text


class TestFrontendCoverageCI:
    def test_dashboard_frontend_ci_runs_coverage(self):
        text = (WORKFLOWS_DIR / "dashboard-frontend-ci.yml").read_text(encoding="utf-8")
        assert "vitest run --coverage" in text

    def test_dashboard_frontend_ci_uploads_codecov_lcov(self):
        text = (WORKFLOWS_DIR / "dashboard-frontend-ci.yml").read_text(encoding="utf-8")
        assert "codecov/codecov-action@v5" in text
        assert "coverage/lcov.info" in text
        assert "flags: frontend" in text

    def test_codecov_yml_frontend_flag(self):
        data = yaml.safe_load((REPO_ROOT / "novel-factory" / "codecov.yml").read_text(encoding="utf-8"))
        assert "frontend" in data["flags"]
        paths = data["flags"]["frontend"]["paths"]
        assert any("dashboard/frontend/src" in p for p in paths)


class TestFrontendCoveragePages:
    def test_coverage_pages_workflow_exists(self):
        wf = WORKFLOWS_DIR / "dashboard-frontend-coverage-pages.yml"
        assert wf.is_file()
        text = wf.read_text(encoding="utf-8")
        assert "upload-pages-artifact" in text
        assert "coverage/html" in text
        assert "deploy-pages" in text

    def test_handoff_has_codecov_badge(self):
        text = (REPO_ROOT / "HANDOFF.md").read_text(encoding="utf-8")
        assert "codecov.io/gh/XiaZiHunDun/LingWen" in text
        assert "flag=frontend" in text
