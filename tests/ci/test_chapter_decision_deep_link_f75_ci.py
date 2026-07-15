"""Phase 9.83 F75: CI contract — chapter decision deep link."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOVEL_FACTORY = REPO_ROOT
FRONTEND = NOVEL_FACTORY / "dashboard" / "frontend"


class TestChapterDecisionDeepLinkF75:
    def test_chapter_decision_link_util(self):
        util = FRONTEND / "src" / "utils" / "chapterDecisionLink.js"
        assert util.is_file()
        assert "findPendingDecisionForChapter" in util.read_text(encoding="utf-8")

    def test_dashboard_nav_composable(self):
        nav = FRONTEND / "src" / "composables" / "useDashboardNav.js"
        assert nav.is_file()

    def test_decisions_page_focus_banner(self):
        page = FRONTEND / "src" / "pages" / "DecisionsPage.vue"
        assert "decision-focus-banner" in page.read_text(encoding="utf-8")

    def test_chapters_page_decision_link(self):
        page = FRONTEND / "src" / "pages" / "ChaptersPage.vue"
        text = page.read_text(encoding="utf-8")
        assert "onChapterDecisionLink" in text
        assert "decision-link-chapters" in text

    def test_vitest_spec_exists(self):
        assert (FRONTEND / "tests" / "unit" / "chapter-decision-link.spec.js").is_file()
