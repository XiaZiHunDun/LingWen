"""Tests for merge preset conflict fix suggestions and apply."""
from __future__ import annotations

import pytest

from infra.creator_merge_preferences import (
    apply_merge_preset_fix,
    detect_merge_preset_conflicts,
    import_merge_preset_packages,
    suggest_merge_preset_fixes,
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


def test_suggest_and_apply_remove_dependency_fix(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="preset-fix",
        title="修复",
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
    fixes = suggest_merge_preset_fixes(root)
    assert fixes["fix_count"] >= 1
    fix = fixes["fixes"][0]
    assert fix["action"] == "remove_dependency"
    applied = apply_merge_preset_fix(
        root,
        package_id=fix["package_id"],
        action=fix["action"],
        dependency_id=fix.get("dependency_id"),
    )
    assert applied["action"] == "remove_dependency"
    remaining = detect_merge_preset_conflicts(root)
    assert remaining["conflict_count"] == 0
    ProjectPaths.reset()
