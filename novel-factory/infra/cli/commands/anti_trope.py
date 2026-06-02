"""anti-trope command - Generate anti-trope creative options for outlines.

Mirrors lines 588-648 of the original infra/cli/commands.py.
"""
from infra.cli.options import UnifiedOptions
from .base import Command


class AntiTropeCommand(Command):
    """反套路创意生成命令"""

    name = "anti-trope"
    description = "生成反套路创意选项"

    def execute(self, options: UnifiedOptions) -> int:
        """
        Execute anti-trope generation.

        Args:
            options: AntiTropeOptions with outline, count, format

        Returns:
            Exit code
        """
        outline = getattr(options, 'outline', '')
        count = getattr(options, 'count', 3)
        format_output = getattr(options, 'format', True)

        if not outline:
            print("[错误] 需要提供 --outline 参数")
            return 1

        print(f"反套路创意生成 | 数量: {count}")
        print(f"大纲: {outline[:100]}...")

        return self._generate_anti_trope(outline, count, format_output)

    def _generate_anti_trope(self, outline: str, count: int, format_output: bool) -> int:
        """Run anti-trope generation"""
        try:
            from tools.anti_trope_enhancer import AntiTropeEnhancer

            enhancer = AntiTropeEnhancer()
            options_list = enhancer.generate_options(outline, count)

            if not options_list:
                print("[错误] 生成失败")
                return 1

            if format_output:
                print(enhancer.format_options(options_list))
            else:
                import json
                print(json.dumps([{
                    "setting": o.setting,
                    "conflict": o.conflict,
                    "character": o.character,
                    "twist": o.twist,
                    "anti_trope_tags": o.anti_trope_tags,
                } for o in options_list], ensure_ascii=False, indent=2))

            return 0

        except ImportError as e:
            print(f"[错误] AntiTropeEnhancer 不可用: {e}")
            return 1
        except Exception as e:
            print(f"[错误] 生成失败: {e}")
            return 1
