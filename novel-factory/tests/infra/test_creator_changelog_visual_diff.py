"""Tests for template changelog visual diff."""
from __future__ import annotations

import pytest

from infra.creator_volume_templates import (
    get_template_version_changelog,
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


def test_changelog_includes_visual_diff(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="visual-diff",
        title="可视化",
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
    entries = get_template_version_changelog(root, saved["id"])
    assert entries[0]["visual_diff"]["lines"]
    ProjectPaths.reset()
