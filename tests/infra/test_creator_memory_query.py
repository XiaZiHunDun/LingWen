"""Tests for creator_memory_query."""
from __future__ import annotations

from infra.creator_memory_query import creator_memory_query
from infra.paths import ProjectPaths
from infra.project_init import init_minimal_short_project
from infra.studio_registry import StudioProject


def test_local_fallback_search(tmp_path):
    ProjectPaths.reset()
    factory = tmp_path / "factory"
    factory.mkdir()
    (factory / "infra").mkdir()
    result = init_minimal_short_project(
        slug="mem-q",
        title="记忆查询",
        factory_root=factory,
        creation_mode="companion",
        chapter_count=3,
    )
    paths = ProjectPaths.get(result.root)
    paths.write_chapter(1, "李逍遥在王宫遇见神秘剑客。")
    project = StudioProject(
        slug=result.slug,
        name=result.title,
        role="production",
        root=result.root,
        location="projects",
    )
    payload = creator_memory_query(project, query="李逍遥", top_k=5)
    assert payload["used_fallback"] is True
    assert payload["results"]
    assert payload["results"][0].get("citation")
    assert "matched_terms" in payload["results"][0]
    ProjectPaths.reset()
