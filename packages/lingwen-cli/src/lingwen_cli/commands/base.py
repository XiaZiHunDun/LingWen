"""Command base class - shared infrastructure for all 10 CLI commands.

Mirrors lines 28-71 of the original infra/cli/commands.py. Each concrete
command (check/repair/verify/etc.) imports from this module and inherits the
`Command` ABC plus the get_range/format_chapter_summary helpers.
"""

from abc import ABC, abstractmethod
from typing import List

from lingwen_paths import ProjectPaths

from lingwen_cli.options import UnifiedOptions
from lingwen_cli.output import OutputFormatter
from lingwen_cli.project_range import project_max_chapter
from lingwen_cli.range_parser import RangeParser


class Command(ABC):
    """Base class for all CLI commands"""

    name: str = ""
    description: str = ""

    def __init__(self):
        # Phase 58: lazy-init paths/range_parser/formatter. Constructing a Command
        # should not require a valid project layout (chapters dir + ProjectPaths.get
        # validation); only executing a command should. Production code accesses
        # these via self.paths.X etc. which triggers resolution on first access.
        # Tests that mock the inner work (BackfillCommand/RippleScanCommand with
        # fully-mocked LLMScanner/Backfiller/storage) can construct without a
        # real project.
        self._paths: ProjectPaths | None = None
        self._range_parser: RangeParser | None = None
        self._formatter: OutputFormatter | None = None

    @property
    def paths(self) -> ProjectPaths:
        """Lazy ProjectPaths singleton (resolved on first access)."""
        if self._paths is None:
            self._paths = ProjectPaths.get()
        return self._paths

    @property
    def range_parser(self) -> RangeParser:
        """Lazy RangeParser (depends on project max chapter)."""
        if self._range_parser is None:
            max_ch = project_max_chapter(self.paths)
            self._range_parser = RangeParser(all_chapters=max_ch)
        return self._range_parser

    @property
    def formatter(self) -> OutputFormatter:
        """Lazy OutputFormatter (no dependencies)."""
        if self._formatter is None:
            self._formatter = OutputFormatter()
        return self._formatter

    @abstractmethod
    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute the command.

        Args:
            options: Command options

        Returns:
            Exit code (0 for success, non-zero for failure)
        """

    def get_range(self, options: UnifiedOptions) -> List[int]:
        """
        Get chapter range from options.

        Args:
            options: UnifiedOptions with range attribute

        Returns:
            List of chapter numbers
        """
        if options.range:
            # Parse from string list
            range_str = ",".join(str(r) for r in options.range)
            return self.range_parser.parse(range_str)

        max_ch = project_max_chapter(self.paths)
        return list(range(1, max_ch + 1))

    def format_chapter_summary(self, chapters: List[int]) -> str:
        """Format chapter range summary"""
        return self.formatter.format_chapters_summary(chapters)
