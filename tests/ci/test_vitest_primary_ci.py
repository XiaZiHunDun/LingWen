"""Phase 12.07: Vitest blocking gate in primary test workflow."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT


class TestVitestPrimaryCi:
    def test_primary_test_workflow_includes_vitest_job(self):
        wf = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        assert "vitest:" in wf
        assert "pnpm vitest run" in wf
        assert "pnpm lint:all" in wf
        assert "pnpm build" in wf
        assert "pnpm/action-setup@v4" in wf

    def test_vitest_script_unchanged(self):
        import json

        pkg = json.loads(
            (NOVEL_FACTORY / "dashboard" / "frontend" / "package.json").read_text(encoding="utf-8"),
        )
        assert pkg["scripts"]["test"] == "vitest run"
