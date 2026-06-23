"""Tests for template version changelog."""
from __future__ import annotations

import pytest

from infra.creator_volume_templates import (
    get_template_version_changelog,
    save_custom_volume_template,
    set_custom_template_version_label,
)
from infra.project_init import init_minimal_short_project
from infra.paths import ProjectPaths


@pytest.fixture
def factory_tmp(tmp_path):
    ProjectPaths.reset()
    factory = tmp_path / "factory"
    factory.mkdir()
    (factory / "infra").mkdir()
    yield factory
    ProjectPaths.reset()


def test_version_changelog_on_set_label(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="changelog-tpl",
        title="变更日志",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    volumes = [
        {"label": "一", "start_chapter": 1, "end_chapter": 12, "core_conflict": "x", "locked": False},
    ]
    saved = save_custom_volume_template(root, name="结构", volumes=volumes, max_chapter=12)
    set_custom_template_version_label(root, saved["id"], version_label="v1.0.0")
    store_path = root / ".state" / "custom_volume_templates.json"
    import json
    store = json.loads(store_path.read_text(encoding="utf-8"))
    for item in store["templates"]:
        if item["id"] == saved["id"]:
            item["volumes"][0]["label"] = "新版"
    store_path.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    set_custom_template_version_label(root, saved["id"], version_label="v1.1.0")
    entries = get_template_version_changelog(root, saved["id"])
    assert len(entries) >= 2
    assert entries[0]["version_label"] == "v1.1.0"
    assert entries[0]["diff_summary"]["changed"] is True
    ProjectPaths.reset()
