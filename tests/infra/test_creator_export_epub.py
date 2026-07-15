"""Tests for creator_export_epub."""
from __future__ import annotations

import zipfile
from io import BytesIO

import pytest

from infra.creator_export_epub import build_creator_epub_bytes
from infra.paths import ProjectPaths
from infra.project_init import init_minimal_short_project
from infra.studio_registry import StudioProject


@pytest.fixture
def mini_project(tmp_path):
    ProjectPaths.reset()
    factory = tmp_path / "factory"
    factory.mkdir()
    (factory / "infra").mkdir()
    result = init_minimal_short_project(
        slug="epub-test",
        title="EPUB测试",
        factory_root=factory,
        creation_mode="companion",
        chapter_count=3,
    )
    paths = ProjectPaths.get(result.root)
    paths.write_chapter(1, "第一章\n\n正文段落。")
    project = StudioProject(
        slug=result.slug,
        name=result.title,
        role="production",
        root=result.root,
        location="projects",
    )
    yield project
    ProjectPaths.reset()


def test_build_epub_zip(mini_project: StudioProject) -> None:
    data = build_creator_epub_bytes(mini_project, mode="full", title="测试书")
    assert data[:2] == b"PK"
    with zipfile.ZipFile(BytesIO(data)) as zf:
        names = zf.namelist()
        assert "mimetype" in names
        assert "OEBPS/content.opf" in names
        assert any(n.endswith("ch001.xhtml") for n in names)
