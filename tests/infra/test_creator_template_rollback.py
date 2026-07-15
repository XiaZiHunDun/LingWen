"""Tests for template version rollback."""
from __future__ import annotations

import pytest

from infra.creator_volume_templates import (
    get_template_version_changelog,
    rollback_template_version,
    save_custom_volume_template,
    set_custom_template_version_label,
)
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


def test_rollback_template_version_restores_volumes(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="rollback-vol",
        title="回滚",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    volumes_v1 = [
        {"label": "一", "start_chapter": 1, "end_chapter": 6, "core_conflict": "a", "locked": False},
        {"label": "二", "start_chapter": 7, "end_chapter": 12, "core_conflict": "b", "locked": False},
    ]
    saved = save_custom_volume_template(root, name="结构", volumes=volumes_v1, max_chapter=12)
    set_custom_template_version_label(root, saved["id"], version_label="v1.0.0")

    volumes_v2 = [
        {"label": "一", "start_chapter": 1, "end_chapter": 12, "core_conflict": "merged", "locked": False},
    ]
    from infra.creator_volume_templates import rename_custom_volume_template

    rename_custom_volume_template(
        root,
        saved["id"],
        name="结构",
        version_label="v2.0.0",
    )
    store_path = root / ".state" / "custom_volume_templates.json"
    import json

    store = json.loads(store_path.read_text(encoding="utf-8"))
    store["templates"][0]["volumes"] = volumes_v2
    store_path.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rolled = rollback_template_version(root, saved["id"], version_label="v1.0.0")
    assert rolled["rolled_back_to"] == "v1.0.0"
    store = json.loads(store_path.read_text(encoding="utf-8"))
    restored = store["templates"][0]["volumes"]
    assert len(restored) == 2
    assert restored[0]["core_conflict"] == "a"
    entries = get_template_version_changelog(root, saved["id"])
    assert entries[0]["can_rollback"] is True
    ProjectPaths.reset()
