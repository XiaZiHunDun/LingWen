"""Phase 9.69 F61: CI contract — human review resolve → resume smoke."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"


class TestHumanReviewSmokeF61Contract:
    def test_runbook_has_human_review_section(self):
        path = NOVEL_FACTORY / "docs" / "chapter-production-runbook.md"
        text = path.read_text(encoding="utf-8")
        assert "人审后恢复" in text
        assert "run_human_review_smoke" in text

    def test_dashboard_smoke_test_exists(self):
        spec = NOVEL_FACTORY / "tests" / "dashboard" / "test_human_review_smoke.py"
        assert spec.is_file()

    def test_golden_path_exports_smoke_helper(self):
        mod = NOVEL_FACTORY / "infra" / "agent_system" / "chapter_golden_path.py"
        text = mod.read_text(encoding="utf-8")
        assert "HumanReviewSmokeResult" in text
        assert "create_golden_dashboard_client" in text
