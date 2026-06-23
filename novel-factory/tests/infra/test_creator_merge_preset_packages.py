"""Tests for merge strategy preset packages."""
from __future__ import annotations

import pytest

from infra.creator_merge_preferences import (
    get_merge_preset_package,
    list_merge_preset_packages,
    save_merge_preset_package,
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


def test_builtin_merge_preset_packages(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="merge-pkg",
        title="预设包",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    packages = list_merge_preset_packages(root)
    assert any(pkg["id"] == "all_disk" for pkg in packages)
    disk = get_merge_preset_package(root, "all_disk")
    assert disk["pillars_merge_source"] == "disk"
    assert disk["scope"] == "builtin"
    ProjectPaths.reset()


def test_save_custom_merge_preset_package(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="merge-pkg-custom",
        title="自定义预设",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    saved = save_merge_preset_package(
        root,
        package_id="my_combo",
        name="我的组合",
        pillars_merge_source="disk",
        global_outline_merge_source="editor",
    )
    assert saved["id"] == "my_combo"
    assert get_merge_preset_package(root, "my_combo")["name"] == "我的组合"
    ProjectPaths.reset()


def test_export_import_merge_preset_packages(factory_tmp) -> None:
    from infra.creator_merge_preferences import (
        export_merge_preset_packages,
        import_merge_preset_packages,
    )

    result = init_minimal_short_project(
        slug="merge-pkg-share",
        title="分享预设",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    save_merge_preset_package(
        root,
        package_id="shared_combo",
        name="分享组合",
        pillars_merge_source="disk",
        global_outline_merge_source="editor",
    )
    exported = export_merge_preset_packages(root)
    assert exported["count"] == 1
    other = init_minimal_short_project(
        slug="merge-pkg-target",
        title="目标",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    imported = import_merge_preset_packages(other.root, exported)
    assert imported["imported"] == 1
    assert get_merge_preset_package(other.root, "shared_combo")["name"] == "分享组合"
    ProjectPaths.reset()


def test_factory_merge_preset_publish_and_pull(factory_tmp, monkeypatch) -> None:
    import infra.creator_merge_preferences as cmp

    monkeypatch.setattr("infra.studio_registry.factory_root", lambda: factory_tmp)
    monkeypatch.setattr(
        cmp,
        "_factory_preset_packages_path",
        lambda: factory_tmp / "infra" / ".state" / "factory_merge_preset_packages.json",
    )
    from infra.creator_merge_preferences import (
        list_factory_merge_preset_packages,
        publish_merge_preset_to_factory,
        pull_factory_merge_presets_to_project,
    )

    result = init_minimal_short_project(
        slug="factory-pkg-src",
        title="工厂源",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    save_merge_preset_package(
        root,
        package_id="team_combo",
        name="团队组合",
        pillars_merge_source="disk",
        global_outline_merge_source="editor",
    )
    published = publish_merge_preset_to_factory(root, "team_combo")
    assert published["scope"] == "factory"
    assert len(list_factory_merge_preset_packages()) == 1
    target = init_minimal_short_project(
        slug="factory-pkg-dst",
        title="工厂目标",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    pulled = pull_factory_merge_presets_to_project(
        target.root,
        package_ids=[published["id"]],
    )
    assert pulled["imported"] == 1
    assert get_merge_preset_package(target.root, "team_combo")["name"] == "团队组合"
    ProjectPaths.reset()
