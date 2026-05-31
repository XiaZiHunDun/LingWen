"""Tests for StoryContractPaths."""

from pathlib import Path

import pytest

from infra.story_contracts.paths import StoryContractPaths


class TestStoryContractPaths:
    """Tests for StoryContractPaths path management."""

    def test_paths_live_under_project_root(self, tmp_path: Path):
        """Verifies all paths under .story-system/."""
        paths = StoryContractPaths.from_project_root(tmp_path)

        # All paths should be under .story-system/
        assert paths.root == tmp_path / ".story-system"
        assert paths.chapters_dir == tmp_path / ".story-system" / "chapters"
        assert paths.master_json == tmp_path / ".story-system" / "MASTER_SETTING.json"
        assert paths.master_md == tmp_path / ".story-system" / "MASTER_SETTING.md"
        assert paths.anti_patterns_json == tmp_path / ".story-system" / "anti_patterns.json"
        assert paths.anti_patterns_md == tmp_path / ".story-system" / "anti_patterns.md"

        # Chapter paths should also be under .story-system/chapters/
        for chapter in [1, 50, 360]:
            chapter_path = paths.chapter_json(chapter)
            assert str(chapter_path).startswith(str(tmp_path / ".story-system"))
            assert chapter_path.parent == paths.chapters_dir
            assert chapter_path.name == f"chapter_{chapter:03d}.json"

            md_path = paths.chapter_md(chapter)
            assert str(md_path).startswith(str(tmp_path / ".story-system"))
            assert md_path.parent == paths.chapters_dir
            assert md_path.name == f"chapter_{chapter:03d}.md"

    def test_paths_from_string_expands_user(self):
        """Verifies Path expansion works with ~ user home."""
        # Using a path with ~ should expand to user home
        paths = StoryContractPaths.from_project_root("~/novel-project")

        assert paths.project_root == Path.home() / "novel-project"
        assert ".story-system" in str(paths.root)
        assert paths.root.parent == paths.project_root

    def test_chapter_path_formatting(self, tmp_path: Path):
        """Verifies chapter numbers are zero-padded to 3 digits."""
        paths = StoryContractPaths.from_project_root(tmp_path)

        assert paths.chapter_json(1) == tmp_path / ".story-system/chapters/chapter_001.json"
        assert paths.chapter_json(50) == tmp_path / ".story-system/chapters/chapter_050.json"
        assert paths.chapter_json(360) == tmp_path / ".story-system/chapters/chapter_360.json"
        assert paths.chapter_md(1) == tmp_path / ".story-system/chapters/chapter_001.md"
        assert paths.chapter_md(99) == tmp_path / ".story-system/chapters/chapter_099.md"

    def test_instance_is_frozen(self, tmp_path: Path):
        """Verifies the dataclass is frozen/immutable."""
        paths = StoryContractPaths.from_project_root(tmp_path)

        with pytest.raises(Exception):  # dataclasses are frozen
            paths.project_root = Path("/other")  # type: ignore