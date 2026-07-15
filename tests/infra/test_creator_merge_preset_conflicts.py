"""Tests for merge preset package conflict detection."""
from __future__ import annotations

import pytest

from infra.creator_merge_preferences import (
    detect_merge_preset_conflicts,
    import_merge_preset_packages,
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


def test_detect_missing_dependency_conflict(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="preset-conflict",
        title="冲突检测",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    import_merge_preset_packages(
        root,
        {
            "packages": [
                {
                    "id": "broken_pkg",
                    "name": "缺依赖",
                    "depends_on": ["missing_pkg"],
                    "pillars_merge_source": "disk",
                    "global_outline_merge_source": "editor",
                },
            ],
        },
    )
    report = detect_merge_preset_conflicts(root)
    types = {row["type"] for row in report["conflicts"]}
    assert "missing_dependency" in types
    assert report["conflict_count"] >= 1
    ProjectPaths.reset()


def test_detect_semver_downgrade_conflict(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="preset-semver-conflict",
        title="semver 冲突",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    import_merge_preset_packages(
        root,
        {
            "packages": [
                {
                    "id": "newer_dep",
                    "name": "新依赖",
                    "version_label": "v2.0.0",
                    "pillars_merge_source": "disk",
                    "global_outline_merge_source": "editor",
                },
                {
                    "id": "older_pkg",
                    "name": "旧包",
                    "version_label": "v1.0.0",
                    "depends_on": ["newer_dep"],
                    "pillars_merge_source": "disk",
                    "global_outline_merge_source": "editor",
                },
            ],
        },
    )
    report = detect_merge_preset_conflicts(root)
    types = {row["type"] for row in report["conflicts"]}
    assert "semver_downgrade" in types
    ProjectPaths.reset()
