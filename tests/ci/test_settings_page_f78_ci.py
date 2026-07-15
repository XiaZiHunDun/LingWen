"""Phase 9.86 F78: CI contract — Settings budget write UI."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOVEL_FACTORY = REPO_ROOT
FRONTEND = NOVEL_FACTORY / "dashboard" / "frontend"


class TestSettingsPageF78:
    def test_settings_page_has_budget_edit_panel(self):
        page = FRONTEND / "src" / "pages" / "SettingsPage.vue"
        text = page.read_text(encoding="utf-8")
        assert "budget-edit-panel" in text
        assert "setBudget" in text
        assert "setBudgetByTier" in text
        assert "只读" not in text or "per-run" in text

    def test_budget_edit_utils_exist(self):
        assert (FRONTEND / "src" / "utils" / "settingsBudgetEdit.js").is_file()

    def test_api_set_budget_functions(self):
        api = FRONTEND / "src" / "api" / "index.js"
        text = api.read_text(encoding="utf-8")
        assert "export async function setBudget" in text
        assert "export async function setBudgetByTier" in text
        assert "method: 'PUT'" in text

    def test_vitest_specs_exist(self):
        assert (FRONTEND / "tests" / "unit" / "settings-budget-edit.spec.js").is_file()
        spec = FRONTEND / "tests" / "unit" / "settings-page.spec.ts"
        assert "setBudget" in spec.read_text(encoding="utf-8")

    def test_v8_roadmap_marks_f78(self):
        roadmap = (
            NOVEL_FACTORY
            / "docs"
            / "superpowers"
            / "plans"
            / "2026-06-11-followup-roadmap-v8-post-9.84.md"
        )
        assert roadmap.is_file()
        text = roadmap.read_text(encoding="utf-8")
        assert "F78" in text
        assert "Settings 预算写入" in text
