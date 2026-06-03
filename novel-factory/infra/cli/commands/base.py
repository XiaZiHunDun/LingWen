"""Command base class - shared infrastructure for all 10 CLI commands.

Mirrors lines 28-71 of the original infra/cli/commands.py. Each concrete
command (check/repair/verify/etc.) imports from this module and inherits the
`Command` ABC plus the get_range/format_chapter_summary helpers.
"""
from abc import ABC, abstractmethod
from typing import List

from infra.cli.options import UnifiedOptions
from infra.cli.output import OutputFormatter
from infra.cli.range_parser import RangeParser
from infra.paths import ProjectPaths


class Command(ABC):
    """Base class for all CLI commands"""

    name: str = ""
    description: str = ""

    def __init__(self):
        self.paths = ProjectPaths.get()
        self.range_parser = RangeParser()
        self.formatter = OutputFormatter()

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
        else:
            # Default to all chapters
            return list(range(1, 361))

    def format_chapter_summary(self, chapters: List[int]) -> str:
        """Format chapter range summary"""
        return self.formatter.format_chapters_summary(chapters)
