"""Tests for infra.creator_volume_templates."""
from __future__ import annotations

import pytest

from infra.paths import ProjectPaths
from infra.creator_volume_templates import (
    build_volume_template,
    delete_custom_volume_template,
    export_custom_volume_templates,
    import_custom_volume_templates,
    list_factory_volume_templates,
    list_template_sync_sources,
    publish_custom_to_factory_library,
    pull_factory_templates_to_project,
    sync_custom_volume_templates_from_projects,
    list_volume_templates,
    rename_custom_volume_template,
    save_custom_volume_template,
    set_custom_template_version_label,
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
    versioned = set_custom_template_version_label(root, saved["id"], version_label="v1.0")
    assert versioned["version_label"] == "v1.0.0"
    rows = list_volume_templates(root)
    match = next(row for row in rows if row["id"] == saved["id"])
    assert match["version_label"] == "v1.0.0"
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


def test_export_import_custom_templates(factory_tmp):
    from infra.project_init import init_minimal_short_project

    result = init_minimal_short_project(
        slug="tpl-io",
        title="导入导出",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    volumes = [
        {"label": "A", "start_chapter": 1, "end_chapter": 12, "core_conflict": "x", "locked": False},
    ]
    save_custom_volume_template(root, name="导出源", volumes=volumes, max_chapter=12)
    exported = export_custom_volume_templates(root)
    assert exported["count"] == 1
    delete_custom_volume_template(root, exported["templates"][0]["id"])
    imported = import_custom_volume_templates(root, exported)
    assert imported["imported"] == 1
    assert len(list_volume_templates(root)) >= 4
    ProjectPaths.reset()


def test_sync_templates_from_other_project(factory_tmp, monkeypatch):
    from infra.project_init import init_minimal_short_project
    from infra.studio_registry import StudioProject

    source = init_minimal_short_project(
        slug="tpl-source",
        title="源项目",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    target = init_minimal_short_project(
        slug="tpl-target",
        title="目标项目",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    volumes = [
        {"label": "A", "start_chapter": 1, "end_chapter": 12, "core_conflict": "x", "locked": False},
    ]
    save_custom_volume_template(source.root, name="共享结构", volumes=volumes, max_chapter=12)
    monkeypatch.setattr(
        "infra.studio_registry.list_projects",
        lambda: [
            StudioProject(
                slug="tpl-source",
                name="源项目",
                role="production",
                root=source.root,
                location="projects",
            ),
            StudioProject(
                slug="tpl-target",
                name="目标项目",
                role="production",
                root=target.root,
                location="projects",
            ),
        ],
    )
    sources = list_template_sync_sources(exclude_slug="tpl-target")
    assert any(row["slug"] == "tpl-source" for row in sources)
    synced = sync_custom_volume_templates_from_projects(
        target.root,
        source_slugs=["tpl-source"],
        exclude_slug="tpl-target",
    )
    assert synced["imported"] == 1
    names = [row["name"] for row in list_volume_templates(target.root) if not row["builtin"]]
    assert any("共享结构" in name for name in names)
    ProjectPaths.reset()


def test_factory_template_publish_pull(factory_tmp, monkeypatch):
    import infra.creator_volume_templates as cvt
    from infra.project_init import init_minimal_short_project

    monkeypatch.setattr("infra.studio_registry.factory_root", lambda: factory_tmp)
    monkeypatch.setattr(
        cvt,
        "_factory_templates_path",
        lambda: factory_tmp / "infra" / ".state" / "factory_volume_templates.json",
    )

    source = init_minimal_short_project(
        slug="factory-src",
        title="工厂源",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    target = init_minimal_short_project(
        slug="factory-tgt",
        title="工厂目标",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    volumes = [
        {"label": "A", "start_chapter": 1, "end_chapter": 12, "core_conflict": "x", "locked": False},
    ]
    saved = save_custom_volume_template(source.root, name="工厂结构", volumes=volumes, max_chapter=12)
    published = publish_custom_to_factory_library(source.root, saved["id"])
    assert published["id"].startswith("factory_")
    assert len(list_factory_volume_templates()) == 1
    built = build_volume_template(published["id"], 24, source.root)
    assert built[-1]["end_chapter"] == 24
    pulled = pull_factory_templates_to_project(target.root, template_ids=[published["id"]])
    assert pulled["imported"] == 1
    ProjectPaths.reset()


@pytest.fixture
def factory_tmp(tmp_path):
    ProjectPaths.reset()
    factory = tmp_path / "factory"
    factory.mkdir()
    (factory / "infra").mkdir()
    yield factory
    ProjectPaths.reset()
