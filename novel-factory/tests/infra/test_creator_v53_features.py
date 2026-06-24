"""Tests for creator v5.3 diff outline side-by-side, batch export, wizard collapse memory."""
from __future__ import annotations

import pytest

from infra.creator_onboarding_progress import load_onboarding_progress, save_wizard_panel_collapsed
from infra.creator_ui_profile import resolve_creator_ui_profile
from infra.creator_volume_plan import volume_plan_diff_payload
from infra.paths import ProjectPaths
from infra.project_init import init_minimal_short_project


@pytest.fixture
def factory_tmp(tmp_path):
    ProjectPaths.reset()
    factory = tmp_path / "factory"
    factory.mkdir()
    (factory / "infra").mkdir()
    yield factory
    ProjectPaths.reset()


def test_advance_v53_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="advance")
    assert profile["volume_plan_diff_outline_side_by_side"] is True
    assert profile["batch_history_export"] is True


def test_studio_v53_ui_profile() -> None:
    profile = resolve_creator_ui_profile(creation_mode="studio")
    assert profile["studio_wizard_collapse_memory"] is True


def test_volume_plan_diff_payload_includes_outline(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v53-diff",
        title="diff",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=5,
    )
    outline_path = result.root / "03_内容仓库" / "01_全文总体大纲" / "全局大纲.md"
    outline_path.parent.mkdir(parents=True, exist_ok=True)
    outline_path.write_text("# 全局\n\n卷一开篇\n", encoding="utf-8")
    draft = [
        {
            "label": "一",
            "start_chapter": 1,
            "end_chapter": 5,
            "core_conflict": "改写",
            "locked": False,
        },
    ]
    payload = volume_plan_diff_payload(result.root, draft)
    assert "global_outline_excerpt" in payload
    assert "全局" in payload["global_outline_excerpt"]
    assert payload["global_outline_path"].endswith("全局大纲.md")


def test_save_wizard_panel_collapsed_persists(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="v53-wizard",
        title="wizard",
        factory_root=factory_tmp,
        creation_mode="studio",
        chapter_count=10,
    )
    saved = save_wizard_panel_collapsed(result.root, collapsed=True)
    assert saved["wizard_panel_collapsed"] is True
    loaded = load_onboarding_progress(result.root)
    assert loaded["wizard_panel_collapsed"] is True
