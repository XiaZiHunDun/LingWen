"""polish command - Key chapter polishing using Claude.

Mirrors lines 415-505 of the original infra/cli/commands.py.
"""
from typing import List

from infra.cli.options import PolishOptions, UnifiedOptions

from .base import Command


class PolishCommand(Command):
    """Key chapter polishing command using Claude"""

    name = "polish"
    description = "关键章节Claude深度润色"

    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute key chapter polishing.

        Args:
            options: PolishOptions with chapter, key_type, auto_detect flags

        Returns:
            Exit code
        """
        polish_options = options if isinstance(options, PolishOptions) else PolishOptions()

        if polish_options.chapter:
            chapters = [polish_options.chapter]
        else:
            chapters = self.get_range(polish_options)

        summary = self.format_chapter_summary(chapters)
        print(f"润色命令 | 范围: {summary}")
        print(f"自动检测: {polish_options.auto_detect}")

        return self._polish(chapters, polish_options)

    def _polish(self, chapters: List[int], options: PolishOptions) -> int:
        """Run key chapter polishing"""
        try:
            from tools.claude_key_chapter_polisher import KeyChapterPolisher, KeyChapterType

            print(f"执行关键章节润色: {len(chapters)} 个章节")

            polisher = KeyChapterPolisher()

            polished = 0
            skipped = 0
            errors = []

            for ch in chapters:
                try:
                    # Determine key_type if specified
                    if options.key_type:
                        try:
                            KeyChapterType(options.key_type)
                        except ValueError:
                            print(f"[警告] 未知key_type: {options.key_type}，将自动检测")

                    if options.dry_run:
                        # Dry run mode - just classify
                        result = polisher.polish_chapter(
                            ch, "", dry_run=True
                        )
                        if result.get("polished"):
                            print(f"ch{ch:03d}: [干跑] 将润色 ({result.get('type')})")
                            polished += 1
                        else:
                            print(f"ch{ch:03d}: [干跑] 跳过 ({result.get('reason', '普通章节')})")
                            skipped += 1
                    else:
                        # Actual polishing with backup
                        result = polisher.polish_with_backup(ch)
                        if result.get("polished"):
                            polished += 1
                            print(f"ch{ch:03d}: ✓ 已润色 ({result.get('type')})")
                        else:
                            skipped += 1
                            reason = result.get("reason", result.get("error", "未知原因"))
                            print(f"ch{ch:03d}: ✗ 跳过 ({reason})")
                except Exception as e:
                    errors.append(f"ch{ch:03d}: {e}")
                    print(f"ch{ch:03d}: [错误] {e}")

            print("-" * 50)
            print(f"完成: 润色 {polished}, 跳过 {skipped}")

            if errors:
                print(f"错误: {len(errors)} 个")

            return 0 if len(errors) == 0 else 1

        except ImportError as e:
            print(f"[错误] KeyChapterPolisher 不可用: {e}")
            return 1
        except Exception as e:
            print(f"[错误] 润色执行失败: {e}")
            return 1
