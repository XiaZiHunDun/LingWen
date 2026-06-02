"""story-contract command - Generate story contract (master_setting + anti_patterns).

Mirrors lines 724-782 of the original infra/cli/commands.py.
"""
from pathlib import Path

from infra.cli.options import StoryContractOptions, UnifiedOptions
from .base import Command


class StoryContractCommand(Command):
    """Story contract generation command"""

    name = "story-contract"
    description = "生成故事合约"

    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute story contract generation.

        Args:
            options: StoryContractOptions with query, genre, chapter, persist

        Returns:
            Exit code
        """
        story_opts = options if isinstance(options, StoryContractOptions) else StoryContractOptions()

        print(f"故事合约 | 查询: {story_opts.query or '(无)'}")
        print(f"题材: {story_opts.genre or '(自动)'}")
        print(f"章节: {story_opts.chapter or '(全局)'}")
        print(f"持久化: {story_opts.persist}")

        try:
            from infra.story_contracts import StoryContractEngine

            # Get project root - use current working directory
            project_root = Path.cwd()

            engine = StoryContractEngine(project_root=project_root)

            # Build contract
            payload = engine.build(
                query=story_opts.query or "默认",
                genre=story_opts.genre,
                chapter=story_opts.chapter,
            )

            print("\n合约内容:")
            print(f"  题材: {payload.master_setting['route']['primary_genre']}")
            print(f"  调性: {payload.master_setting['master_constraints']['core_tone']}")
            print(f"  节奏: {payload.master_setting['master_constraints']['pacing_strategy']}")
            print(f"  反套路: {len(payload.anti_patterns)} 条")

            # Persist if requested
            if story_opts.persist:
                engine.persist(payload)
                print(f"\n已保存到: {engine.paths.root}")
                return 0
            else:
                print("\n(未持久化，使用 --persist 保存)")
                return 0

        except ImportError as e:
            print(f"[错误] StoryContractEngine 不可用: {e}")
            return 1
        except Exception as e:
            print(f"[错误] 合约生成失败: {e}")
            return 1
