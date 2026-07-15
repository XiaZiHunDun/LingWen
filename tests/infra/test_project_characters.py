"""Tests for project-scoped character resolution."""
from __future__ import annotations

from infra.paths import ProjectPaths
from infra.project_characters import load_agency_target_characters, load_project_character_names


def test_huiyu_dangan_protagonist_only():
    from pathlib import Path

    ProjectPaths.reset()
    factory = Path(__file__).resolve().parents[1]
    huiyu = factory / "projects" / "huiyu-dangan"
    if not huiyu.is_dir():
        import pytest

        pytest.skip("huiyu-dangan not present")
    paths = ProjectPaths.get(huiyu)
    names = load_project_character_names(paths)
    assert "林栀" in names
    assert "林夜" not in names


def test_testbed_fallback_when_no_profiles(tmp_path):
    ProjectPaths.reset()
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "project.yaml").write_text(
        "project:\n  name: t\n  slug: t\n  role: testbed\n  max_chapter: 360\n",
        encoding="utf-8",
    )
    profiles = tmp_path / "03_内容仓库" / "角色设定"
    profiles.mkdir(parents=True)
    (profiles / "character_profiles.json").write_text('{"characters": []}', encoding="utf-8")
    (tmp_path / "03_内容仓库" / "04_正文").mkdir(parents=True)
    paths = ProjectPaths.get(tmp_path)
    names = load_project_character_names(paths)
    assert "林夜" in names


def test_agency_filters_to_characters_in_chapter(tmp_path):
    ProjectPaths.reset()
    profiles = tmp_path / "03_内容仓库" / "角色设定"
    profiles.mkdir(parents=True)
    (profiles / "character_profiles.json").write_text(
        '{"characters": [{"name": "林栀", "role": "主角"}, {"name": "周姐", "role": "配角"}]}',
        encoding="utf-8",
    )
    (tmp_path / "03_内容仓库" / "04_正文").mkdir(parents=True)
    paths = ProjectPaths.get(tmp_path)
    targets = load_agency_target_characters(
        paths,
        chapter_content="林栀站在便利店门口。",
    )
    assert targets == ["林栀"]
