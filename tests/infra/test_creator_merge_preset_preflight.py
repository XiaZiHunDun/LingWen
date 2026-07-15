"""Tests for merge preset import preflight and batch fix apply."""
from __future__ import annotations

import pytest

from infra.creator_merge_preferences import (
    apply_all_merge_preset_fixes,
    import_merge_preset_packages,
    preflight_merge_preset_import,
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


def test_preflight_blocks_bad_import(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="preflight",
        title="预检",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    report = preflight_merge_preset_import(
        root,
        {
            "packages": [
                {
                    "id": "bad_pkg",
                    "name": "坏包",
                    "depends_on": ["ghost"],
                    "pillars_merge_source": "disk",
                    "global_outline_merge_source": "editor",
                },
            ],
        },
    )
    assert report["blocked"] is True
    assert report["conflict_count"] >= 1
    ProjectPaths.reset()


def test_apply_all_merge_preset_fixes(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="apply-all",
        title="批量修复",
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
                    "id": "broken_all",
                    "name": "批量",
                    "depends_on": ["missing_all"],
                    "pillars_merge_source": "disk",
                    "global_outline_merge_source": "editor",
                },
            ],
        },
    )
    applied = apply_all_merge_preset_fixes(root)
    assert applied["applied"] >= 1
    assert applied["conflict_count"] == 0
    ProjectPaths.reset()
