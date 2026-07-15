"""reading-power command - Reading power analysis (hook + coolpoint counts).

Mirrors lines 930-989 of the original infra/cli/commands.py.
"""
from infra.cli.options import UnifiedOptions

from .base import Command


class ReadingPowerCommand(Command):
    """Reading power analysis command"""

    name = "reading-power"
    description = "追读力分析"

    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute reading power analysis.

        Args:
            options: UnifiedOptions

        Returns:
            Exit code
        """
        try:
            from pathlib import Path

            from infra.reading_power import ReadingPowerEngine
        except ImportError as e:
            print(f"[错误] 追读力模块不可用: {e}")
            return 1

        chapters = self.get_range(options)
        summary = self.format_chapter_summary(chapters)
        print(f"追读力分析 | 范围: {summary}")

        engine = ReadingPowerEngine()
        results = []

        for chapter_num in chapters:
            chapter_path = self.paths.get_chapter_path(chapter_num)
            if not chapter_path.exists():
                print(f"  章节 {chapter_num}: 文件不存在")
                continue

            try:
                with open(chapter_path, encoding="utf-8") as f:
                    content = f.read()

                engine.analyze_chapter(chapter_num, content)
                data = engine.get_chapter_reading_power(chapter_num)
                summary_data = data.get("summary", {})

                hook_count = summary_data.get("hook_count", 0)
                coolpoint_count = summary_data.get("coolpoint_count", 0)

                print(f"  章节 {chapter_num}: {hook_count} 钩子, {coolpoint_count} 爽点")
                results.append((chapter_num, hook_count, coolpoint_count))

            except Exception as e:
                print(f"  章节 {chapter_num}: 分析失败 - {e}")

        # Summary
        if results:
            total_hooks = sum(r[1] for r in results)
            total_coolpoints = sum(r[2] for r in results)
            print(f"\n汇总: {len(results)} 章, {total_hooks} 钩子, {total_coolpoints} 爽点")

        return 0
