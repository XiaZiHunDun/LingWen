"""Tests for merge preset package dependency graph."""
from __future__ import annotations

import pytest

from infra.creator_merge_preferences import build_merge_preset_graph
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


def test_merge_preset_graph_includes_builtin_edges(factory_tmp) -> None:
    result = init_minimal_short_project(
        slug="preset-graph",
        title="依赖图",
        factory_root=factory_tmp,
        creation_mode="advance",
        chapter_count=12,
    )
    root = result.root
    graph = build_merge_preset_graph(root)
    assert graph["node_count"] >= 6
    assert graph["edge_count"] >= 3
    combo_edge = next(
        edge for edge in graph["edges"] if edge["from"] == "pillars_disk_outline_editor"
    )
    assert combo_edge["to"] in {"all_disk", "all_editor"}
    ProjectPaths.reset()
