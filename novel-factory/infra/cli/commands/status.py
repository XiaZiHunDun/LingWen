"""status command - View chapter status (existence + size stats).

Mirrors lines 512-581 of the original infra/cli/commands.py.
"""
from typing import List

from infra.cli.options import UnifiedOptions
from .base import Command


class StatusCommand(Command):
    """Chapter status command"""

    name = "status"
    description = "查看章节状态"

    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute status command.

        Args:
            options: UnifiedOptions

        Returns:
            Exit code
        """
        chapters = self.get_range(options)
        summary = self.format_chapter_summary(chapters)

        print(f"状态命令 | 范围: {summary}")

        return self._show_status(chapters)

    def _show_status(self, chapters: List[int]) -> int:
        """Show status for chapters"""
        print("=" * 60)
        print("章节状态")
        print("=" * 60)

        # Count chapters by state
        total = len(chapters)
        existing = 0
        empty = 0
        sizes = []

        for ch in chapters:
            path = self.paths.get_chapter_path(ch)
            if path.exists():
                existing += 1
                size = path.stat().st_size
                sizes.append(size)
            else:
                empty += 1

        print(f"总计: {total} 章")
        print(f"存在: {existing} 章")
        print(f"缺失: {empty} 章")

        if sizes:
            avg_size = sum(sizes) // len(sizes)
            min_size = min(sizes)
            max_size = max(sizes)
            print(f"大小: 平均 {avg_size} bytes, 最小 {min_size}, 最大 {max_size}")

        print("=" * 60)

        # Show individual chapter status if verbose
        for ch in chapters[:20]:  # Limit output
            path = self.paths.get_chapter_path(ch)
            if path.exists():
                size = path.stat().st_size
                status = "✓" if size > 100 else "⚠"
                print(f"  {status} ch{ch:03d}: {size} bytes")
            else:
                print(f"  ✗ ch{ch:03d}: 缺失")

        if total > 20:
            print(f"  ... 还有 {total - 20} 章")

        return 0
