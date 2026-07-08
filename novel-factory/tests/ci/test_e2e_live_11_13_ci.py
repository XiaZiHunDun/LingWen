"""Phase 11.13: Playwright live-backend 8/8 — WS + CI contract."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"
FRONTEND_CI = REPO_ROOT / ".github" / "workflows" / "dashboard-frontend-ci.yml"
LIVE_BACKEND_SPEC_STEMS = (
    "decisions-resolve",
    "ripples-audit",
    "creator-workspace",
    "ask-flow",
    "library-flow",
    "more-hub",
    "landing-nav",
    "advance-produce",
    "today-flow",
    "insight-flow",
    "studio-flow",
    "settings-flow",
    "workflows-flow",
    "advance-batch-flow",
    "cascade-runs-flow",
    "entity-memory-flow",
    "director-paths-flow",
    "memory-gateway-flow",
    "product-tools-flow",
    "companion-full-path-flow",
)


class TestE2eLive1113:
    def test_pyproject_uvicorn_standard_for_ws(self):
        text = (NOVEL_FACTORY / "pyproject.toml").read_text(encoding="utf-8")
        assert "uvicorn[standard]" in text

    def test_live_backend_project_eight_specs(self):
        specs_dir = NOVEL_FACTORY / "dashboard" / "frontend" / "tests" / "e2e-smoke"
        total = 0
        for stem in LIVE_BACKEND_SPEC_STEMS:
            path = specs_dir / f"{stem}.spec.js"
            assert path.is_file(), f"missing live-backend spec: {path.name}"
            total += path.read_text(encoding="utf-8").count("test(")
        assert total >= 61, f"expected >=61 live-backend tests, got {total}"

    def test_verify_script_playwright_fallback(self):
        script = NOVEL_FACTORY / "scripts" / "verify-e2e-live-ci.sh"
        text = script.read_text(encoding="utf-8")
        assert "playwright install chromium" in text

    def test_duplicate_e2e_live_workflow_removed(self):
        assert not (REPO_ROOT / ".github" / "workflows" / "dashboard-e2e-live.yml").exists()

    def test_primary_test_workflow_includes_e2e_live(self):
        wf = FRONTEND_CI.read_text(encoding="utf-8")
        assert "e2e-live:" in wf
        assert "pnpm e2e:live" in wf
        assert "LINGWEN_E2E_LIVE: \"1\"" in wf or "LINGWEN_E2E_LIVE: '1'" in wf

    def test_live_backend_helper_novel_factory_root(self):
        helper = (
            NOVEL_FACTORY
            / "dashboard"
            / "frontend"
            / "tests"
            / "e2e-smoke"
            / "helpers"
            / "live-backend.js"
        )
        text = helper.read_text(encoding="utf-8")
        assert "../../../../.." in text
        assert "../../../../../.." not in text
