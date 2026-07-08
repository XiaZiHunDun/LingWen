"""Phase 9.71 F63: CI contract — Dashboard chapters page MVP."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"


class TestChaptersPageF63Contract:
    def test_chapters_page_vue_exists(self):
        vue = NOVEL_FACTORY / "dashboard" / "frontend" / "src" / "pages" / "ChaptersPage.vue"
        assert vue.is_file()
        text = vue.read_text(encoding="utf-8")
        assert "chapter-production-status" in text
        assert "incremental_backfill" in text or "chapter-backfill-badge" in text

    def test_app_wires_chapters_page(self):
        page = NOVEL_FACTORY / "dashboard" / "frontend" / "src" / "pages" / "ProducePage.vue"
        text = page.read_text(encoding="utf-8")
        assert "ChaptersPage" in text
        assert "章节管理 - 开发中" not in text

    def test_chapters_page_unit_test_exists(self):
        spec = NOVEL_FACTORY / "dashboard" / "frontend" / "tests" / "unit" / "chapters-page.spec.ts"
        assert spec.is_file()
