"""Tests for ContractPersister JSON/Markdown persistence."""

import json
import tempfile
from pathlib import Path

import pytest

from infra.story_contracts.paths import StoryContractPaths
from infra.story_contracts.persister import ContractPayload, ContractPersister


class TestContractPersister:
    """Tests for ContractPersister class."""

    @pytest.fixture
    def temp_project_root(self) -> Path:
        """Create a temporary project root for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def paths(self, temp_project_root: Path) -> StoryContractPaths:
        """Create StoryContractPaths for testing."""
        return StoryContractPaths(project_root=temp_project_root)

    @pytest.fixture
    def persister(self, paths: StoryContractPaths) -> ContractPersister:
        """Create ContractPersister for testing."""
        return ContractPersister(paths)

    @pytest.fixture
    def sample_payload(self) -> ContractPayload:
        """Create a sample ContractPayload for testing."""
        return ContractPayload(
            master_setting={
                "title": "Test Novel",
                "genre": "fantasy",
                "setting": "medieval world",
            },
            anti_patterns=[
                {"text": "Suddenly, everything changed.", "source_table": "ch001", "source_id": "1"},
                {"text": "It was a dream.", "source_table": "ch002", "source_id": "1"},
            ],
        )

    def test_persist_writes_master_and_anti_patterns(
        self,
        persister: ContractPersister,
        paths: StoryContractPaths,
        sample_payload: ContractPayload,
    ) -> None:
        """Verify files created and content correct."""
        persister.persist(sample_payload)

        # Verify master JSON
        assert paths.master_json.exists()
        master_data = json.loads(paths.master_json.read_text(encoding="utf-8"))
        assert master_data["title"] == "Test Novel"
        assert master_data["genre"] == "fantasy"

        # Verify anti_patterns JSON
        assert paths.anti_patterns_json.exists()
        anti_data = json.loads(paths.anti_patterns_json.read_text(encoding="utf-8"))
        assert len(anti_data) == 2
        assert anti_data[0]["text"] == "Suddenly, everything changed."

    def test_persist_creates_directories(
        self,
        persister: ContractPersister,
        paths: StoryContractPaths,
        sample_payload: ContractPayload,
    ) -> None:
        """Verify directories created."""
        persister.persist(sample_payload)

        # Verify root and chapters_dir created
        assert paths.root.exists()
        assert paths.root.is_dir()
        assert paths.chapters_dir.exists()
        assert paths.chapters_dir.is_dir()

    def test_load_returns_none_if_no_files(
        self,
        persister: ContractPersister,
    ) -> None:
        """Verify None when no files exist."""
        result = persister.load()
        assert result is None

    def test_markdown_writer_preserves_manual_notes_outside_markers(
        self,
        persister: ContractPersister,
        paths: StoryContractPaths,
        sample_payload: ContractPayload,
    ) -> None:
        """Verify marker replacement preserves external content."""
        # First, create the directory and file with manual content and markers
        paths.root.mkdir(parents=True, exist_ok=True)
        manual_intro = "# My Novel Notes\n\nThis is my custom introduction.\n\n"
        paths.master_md.write_text(
            manual_intro
            + "<!-- STORY-SYSTEM:BEGIN -->\n## Old Content\n\nOld data\n<!-- STORY-SYSTEM:END -->\n\n# Appendix\n\nAdditional notes here.",
            encoding="utf-8",
        )

        # Persist new content
        persister.persist(sample_payload)

        # Verify external content preserved
        content = paths.master_md.read_text(encoding="utf-8")
        assert "This is my custom introduction." in content
        assert "# Appendix" in content
        assert "Additional notes here." in content
        # Verify marker content updated
        assert "## Master Setting" in content
        assert "Old Content" not in content

    def test_load_returns_payload(
        self,
        persister: ContractPersister,
        paths: StoryContractPaths,
        sample_payload: ContractPayload,
    ) -> None:
        """Verify load returns correct payload."""
        persister.persist(sample_payload)
        loaded = persister.load()

        assert loaded is not None
        assert loaded.master_setting["title"] == "Test Novel"
        assert len(loaded.anti_patterns) == 2

    def test_persist_with_chapter_brief(
        self,
        persister: ContractPersister,
        paths: StoryContractPaths,
        temp_project_root: Path,
    ) -> None:
        """Verify chapter brief is persisted correctly."""
        payload = ContractPayload(
            master_setting={"title": "Test"},
            anti_patterns=[],
            chapter_brief={
                "chapter_number": 5,
                "title": "Chapter Five",
                "summary": "Test summary",
            },
        )
        persister.persist(payload)

        # Verify chapter JSON created
        assert paths.chapter_json(5).exists()
        chapter_data = json.loads(paths.chapter_json(5).read_text(encoding="utf-8"))
        assert chapter_data["chapter_number"] == 5
        assert chapter_data["title"] == "Chapter Five"
