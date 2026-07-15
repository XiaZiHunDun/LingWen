"""Phase 9.97 F88: CI contract — ChaptersPage latest batch badge."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOVEL_FACTORY = REPO_ROOT
FRONTEND = NOVEL_FACTORY / "dashboard" / "frontend"


class TestChaptersLatestBatchBadgeF88:
    def test_rollup_api_available(self):
        app = NOVEL_FACTORY / "dashboard" / "app.py"
        assert "/api/production-records/rollup" in app.read_text(encoding="utf-8")

    def test_latest_batch_badge_util(self):
        util = FRONTEND / "src" / "utils" / "latestBatchBadge.js"
        text = util.read_text(encoding="utf-8")
        assert util.is_file()
        assert "pickLatestBatch" in text
        assert "formatLatestBatchBadge" in text

    def test_chapters_page_badge(self):
        page = FRONTEND / "src" / "pages" / "ChaptersPage.vue"
        text = page.read_text(encoding="utf-8")
        assert "latest-batch-badge" in text
        assert "fetchProductionRollup" in text

    def test_vitest_specs_exist(self):
        assert (FRONTEND / "tests" / "unit" / "latest-batch-badge.spec.js").is_file()
        spec = FRONTEND / "tests" / "unit" / "chapters-page.spec.ts"
        assert "latest-batch-badge" in spec.read_text(encoding="utf-8")
