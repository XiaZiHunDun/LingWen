"""Tests for infra.cli.project_range."""
from __future__ import annotations

import pytest

from infra.cli.project_range import project_max_chapter
from infra.cli.range_parser import RangeParser
from infra.paths import ProjectPaths


@pytest.fixture
def five_chapter_project(tmp_path):
    ProjectPaths._instance = None
    (tmp_path / "03_内容仓库" / "04_正文").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定").mkdir(parents=True)
    (tmp_path / "03_内容仓库" / "角色设定" / "character_profiles.json").write_text(
        "{}", encoding="utf-8",
    )
    (tmp_path / "config").mkdir(parents=True)
    (tmp_path / "config" / "project.yaml").write_text(
        """
project:
  name: Short
  slug: short
  max_chapter: 5
  pillars_path: docs/novel-pillars.md
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "docs" / "novel-pillars.md").write_text("# p", encoding="utf-8")
    paths = ProjectPaths.get(tmp_path)
    yield paths
    ProjectPaths._instance = None


def test_project_max_chapter_from_yaml(five_chapter_project):
    assert project_max_chapter(five_chapter_project) == 5


def test_range_parser_all_respects_max(five_chapter_project):
    max_ch = project_max_chapter(five_chapter_project)
    chapters = RangeParser(all_chapters=max_ch).parse("all")
    assert chapters == [1, 2, 3, 4, 5]
