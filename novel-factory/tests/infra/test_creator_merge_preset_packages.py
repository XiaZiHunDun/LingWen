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
    assert disk["global_outline_merge_source"] == "disk"
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
