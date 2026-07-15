"""Tests for merge preset package semver labels."""
from __future__ import annotations

import pytest

from infra.creator_merge_preferences import (
    export_merge_preset_packages,
    get_merge_preset_package,
    save_merge_preset_package,
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


def test_merge_preset_package_semver(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="preset-semver",
        title="预设 semver",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    saved = save_merge_preset_package(
        root,
        package_id="semver_combo",
        name="版本组合",
        pillars_merge_source="disk",
        global_outline_merge_source="editor",
        version_label="1.2.0",
    )
    assert saved["version_label"] == "v1.2.0"
    assert saved["version_semver_valid"] is True
    pkg = get_merge_preset_package(root, "semver_combo")
    assert pkg["version_label"] == "v1.2.0"
    exported = export_merge_preset_packages(root)
    assert exported["packages"][0]["version_label"] == "v1.2.0"
    ProjectPaths.reset()
