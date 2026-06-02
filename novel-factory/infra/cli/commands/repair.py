"""repair command - Batch repair (WorldviewRepairer/AITraceRepairer).

Mirrors lines 217-320 of the original infra/cli/commands.py.
"""
from typing import List

from infra.cli.options import RepairOptions, UnifiedOptions
from .base import Command


class RepairCommand(Command):
    """Batch repair command"""

    name = "repair"
    description = "批量修复章节问题"

    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute batch repair.

        Args:
            options: RepairOptions with track, regression flags

        Returns:
            Exit code
        """
        repair_options = options if isinstance(options, RepairOptions) else RepairOptions()
        chapters = self.get_range(repair_options)
        summary = self.format_chapter_summary(chapters)

        print(f"修复命令 | 范围: {summary}")
        print(f"追踪: {repair_options.track}, 回归测试: {repair_options.regression}")

        if repair_options.track == "worldview":
            return self._repair_worldview(chapters, repair_options)
        elif repair_options.track == "ai_trace":
            return self._repair_ai_trace(chapters, repair_options)
        elif repair_options.track == "all":
            return self._repair_all(chapters, repair_options)
        else:
            print(f"[错误] 未知的修复追踪类型: {repair_options.track}")
            return 1

    def _repair_worldview(self, chapters: List[int], options: RepairOptions) -> int:
        """Repair worldview consistency issues"""
        try:
            from infra.quality.repairers.worldview_repairer import WorldviewRepairer

            print(f"执行世界观修复: {len(chapters)} 个章节")

            repairer = WorldviewRepairer()
            return self._run_repair(repairer, chapters, options)

        except ImportError as e:
            print(f"[警告] WorldviewRepairer 不可用: {e}")
            return 1

    def _repair_ai_trace(self, chapters: List[int], options: RepairOptions) -> int:
        """Repair AI trace issues"""
        try:
            from infra.quality.repairers.ai_trace_repairer import AITraceRepairer

            print(f"执行AI痕迹修复: {len(chapters)} 个章节")

            repairer = AITraceRepairer()
            return self._run_repair(repairer, chapters, options)

        except ImportError as e:
            print(f"[警告] AITraceRepairer 不可用: {e}")
            return 1

    def _repair_all(self, chapters: List[int], options: RepairOptions) -> int:
        """Repair all issue types"""
        print("执行全面修复...")

        # Run worldview repair
        result1 = self._repair_worldview(chapters, options)
        # Run ai_trace repair
        result2 = self._repair_ai_trace(chapters, options)

        return result1 or result2

    def _run_repair(self, repairer, chapters: List[int], options: RepairOptions) -> int:
        """Run repairer on chapters"""
        total_changes = 0
        errors = []

        for ch in chapters:
            try:
                if options.dry_run:
                    new_content = repairer.dry_run(ch)
                    content = repairer.paths.read_chapter(ch)
                    if new_content != content:
                        print(f"ch{ch:03d}: [干跑] 预计修改")
                else:
                    result = repairer.repair(ch)
                    if result.success:
                        total_changes += result.changes
                        if result.changes > 0:
                            print(f"ch{ch:03d}: ✓ 修复 {result.changes} 处")
                    else:
                        errors.append(f"ch{ch:03d}: {result.error}")
            except Exception as e:
                errors.append(f"ch{ch:03d}: {e}")

        print("-" * 50)
        print(f"完成: 总修改 {total_changes} 处")

        if errors:
            print(f"错误: {len(errors)} 个")
            for err in errors[:5]:
                print(f"  {err}")

        return 0 if len(errors) == 0 else 1
