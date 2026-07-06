"""Tests for creator_export_docx."""
from __future__ import annotations

import zipfile
from io import BytesIO

import pytest

from infra.creator_export_docx import build_creator_docx_bytes
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
        slug="docx-test",
        title="DOCX测试",
        factory_root=factory,
        creation_mode="companion",
        chapter_count=3,
    )
    paths = ProjectPaths.get(result.root)
    paths.write_chapter(1, "第一章\n\n正文。")
    project = StudioProject(
        slug=result.slug,
        name=result.title,
        role="production",
        root=result.root,
        location="projects",
    )
    yield project
    ProjectPaths.reset()


def test_build_docx_zip(mini_project: StudioProject) -> None:
    data = build_creator_docx_bytes(mini_project, mode="full", author="作者甲")
    assert data[:2] == b"PK"
    with zipfile.ZipFile(BytesIO(data)) as zf:
        assert "word/document.xml" in zf.namelist()
        xml = zf.read("word/document.xml").decode("utf-8")
        assert "作者甲" in xml
        assert "第一章" in xml
