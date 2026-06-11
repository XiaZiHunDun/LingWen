"""Phase 9.78 F68: CI contract — SettingsPage MVP."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOVEL_FACTORY = REPO_ROOT / "novel-factory"
FRONTEND = NOVEL_FACTORY / "dashboard" / "frontend"


class TestSettingsPageF68:
    def test_settings_page_exists(self):
        page = FRONTEND / "src" / "pages" / "SettingsPage.vue"
        assert page.is_file()
        text = page.read_text(encoding="utf-8")
        assert "budget-panel" in text
        assert "env-panel" in text
        assert "budget-edit-panel" in text

    def test_settings_utils_exist(self):
        assert (FRONTEND / "src" / "utils" / "settingsEnv.js").is_file()
        assert (FRONTEND / "src" / "utils" / "settingsBudget.js").is_file()

    def test_api_fetch_budgets(self):
        api = FRONTEND / "src" / "api" / "index.js"
        assert "fetchBudgets" in api.read_text(encoding="utf-8")
        assert "fetchBudgetsByTier" in api.read_text(encoding="utf-8")

    def test_app_wires_settings_page(self):
        app = FRONTEND / "src" / "App.vue"
        text = app.read_text(encoding="utf-8")
        assert "SettingsPage" in text
        assert "系统设置 - 开发中" not in text

    def test_vitest_specs_exist(self):
        assert (FRONTEND / "tests" / "unit" / "settings-page.spec.ts").is_file()
        assert (FRONTEND / "tests" / "unit" / "settings-budget.spec.js").is_file()
