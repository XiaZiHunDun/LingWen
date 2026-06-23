"""Tests for infra.creator_volume_templates."""
from __future__ import annotations

import pytest

from infra.paths import ProjectPaths
from infra.creator_volume_templates import (
    build_volume_template,
    delete_custom_volume_template,
    list_volume_templates,
    rename_custom_volume_template,
    save_custom_volume_template,
)


def test_list_volume_templates():
    rows = list_volume_templates()
    ids = {row["id"] for row in rows}
    assert "three_act" in ids
    assert "five_volume" in ids


def test_build_three_act_template():
    volumes = build_volume_template("three_act", 40)
    assert len(volumes) == 3
    assert volumes[0]["start_chapter"] == 1
    assert volumes[-1]["end_chapter"] == 40


def test_build_companion_short():
    volumes = build_volume_template("companion_short", 12)
    assert len(volumes) == 1
    assert volumes[0]["end_chapter"] == 12


def test_unknown_template():
    with pytest.raises(ValueError):
        build_volume_template("nope", 10)


def test_custom_template_save_and_apply(factory_tmp):
    from infra.project_init import init_minimal_short_project
    from infra.paths import ProjectPaths

    ProjectPaths.reset()
    result = init_minimal_short_project(
        slug="custom-tpl",
        title="自定义模板",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=20,
    )
    root = result.root
    volumes = [
        {"label": "A", "start_chapter": 1, "end_chapter": 10, "core_conflict": "x", "locked": False},
        {"label": "B", "start_chapter": 11, "end_chapter": 20, "core_conflict": "y", "locked": False},
    ]
    saved = save_custom_volume_template(root, name="我的结构", volumes=volumes, max_chapter=20)
    rows = list_volume_templates(root)
    assert any(row["id"] == saved["id"] and not row["builtin"] for row in rows)
    built = build_volume_template(saved["id"], 40, root)
    assert built[-1]["end_chapter"] == 40
    ProjectPaths.reset()


def test_delete_custom_template(factory_tmp):
    from infra.project_init import init_minimal_short_project

    result = init_minimal_short_project(
        slug="del-tpl",
        title="删除模板",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=20,
    )
    root = result.root
    volumes = [
        {"label": "A", "start_chapter": 1, "end_chapter": 20, "core_conflict": "x", "locked": False},
    ]
    saved = save_custom_volume_template(root, name="待删", volumes=volumes, max_chapter=20)
    deleted = delete_custom_volume_template(root, saved["id"])
    assert deleted["deleted"] is True
    rows = list_volume_templates(root)
    assert not any(row["id"] == saved["id"] for row in rows)
    with pytest.raises(ValueError):
        delete_custom_volume_template(root, "three_act")
    ProjectPaths.reset()


def test_rename_custom_template(factory_tmp):
    from infra.project_init import init_minimal_short_project

    result = init_minimal_short_project(
        slug="rename-tpl",
        title="重命名模板",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=20,
    )
    root = result.root
    volumes = [
        {"label": "A", "start_chapter": 1, "end_chapter": 20, "core_conflict": "x", "locked": False},
    ]
    saved = save_custom_volume_template(root, name="旧名", volumes=volumes, max_chapter=20)
    renamed = rename_custom_volume_template(root, saved["id"], name="新名", description="说明")
    assert renamed["name"] == "新名"
    rows = list_volume_templates(root)
    match = next(row for row in rows if row["id"] == saved["id"])
    assert match["name"] == "新名"
    with pytest.raises(ValueError):
        rename_custom_volume_template(root, "three_act", name="不行")
    ProjectPaths.reset()


@pytest.fixture
def factory_tmp(tmp_path):
    ProjectPaths.reset()
    factory = tmp_path / "factory"
    factory.mkdir()
    (factory / "infra").mkdir()
    yield factory
    ProjectPaths.reset()
