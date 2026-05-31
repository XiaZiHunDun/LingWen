"""Path management utilities for Story Contracts persistence."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StoryContractPaths:
    """Manages paths for Story Contracts persistence under .story-system/ directory."""

    project_root: Path

    @classmethod
    def from_project_root(cls, project_root: Path | str) -> "StoryContractPaths":
        """Create instance from project root path, expanding user home if needed."""
        if isinstance(project_root, str):
            project_root = Path(project_root).expanduser()
        else:
            project_root = project_root.expanduser()
        return cls(project_root=project_root)

    @property
    def root(self) -> Path:
        """Root directory for all story contract data (.story-system/)."""
        return self.project_root / ".story-system"

    @property
    def chapters_dir(self) -> Path:
        """Directory containing individual chapter contract files."""
        return self.root / "chapters"

    @property
    def master_json(self) -> Path:
        """Path to MASTER_SETTING.json."""
        return self.root / "MASTER_SETTING.json"

    @property
    def master_md(self) -> Path:
        """Path to MASTER_SETTING.md."""
        return self.root / "MASTER_SETTING.md"

    @property
    def anti_patterns_json(self) -> Path:
        """Path to anti_patterns.json."""
        return self.root / "anti_patterns.json"

    @property
    def anti_patterns_md(self) -> Path:
        """Path to anti_patterns.md."""
        return self.root / "anti_patterns.md"

    def chapter_json(self, chapter: int) -> Path:
        """Path to chapter contract JSON file."""
        return self.chapters_dir / f"chapter_{chapter:03d}.json"

    def chapter_md(self, chapter: int) -> Path:
        """Path to chapter contract Markdown file."""
        return self.chapters_dir / f"chapter_{chapter:03d}.md"