"""init-project command — minimal-short scaffold."""
from pathlib import Path

from infra.cli.options import InitProjectOptions
from infra.project_init import init_minimal_short_project

from .base import Command


class InitProjectCommand(Command):
    name = "init-project"
    description = "新建 minimal-short 项目脚手架"

    def execute(self, options: InitProjectOptions) -> int:
        out = Path(options.out).resolve() if options.out else None
        try:
            result = init_minimal_short_project(
                slug=options.slug,
                title=options.title,
                protagonist=options.protagonist,
                genre=options.genre,
                out_dir=out,
                overwrite=options.overwrite,
            )
        except (ValueError, FileExistsError) as exc:
            print(f"[错误] {exc}")
            return 1

        print("=" * 60)
        print(f"项目已创建: {result.title} ({result.slug})")
        print("=" * 60)
        print(f"  路径: {result.root}")
        print(f"  章节: {result.chapter_count} 章大纲")
        print(f"  文件: {len(result.files_written)} 个")
        print()
        print("下一步:")
        print(f"  export LINGWEN_PROJECT_ROOT={result.root}")
        print("  export LINGWEN_PRODUCTION_MODE=canon")
        print("  python -m infra.agent_system.chapter_production_pilot \\")
        print("    --preflight-only --chapter-num 1")
        print()
        print("  # 生产前请编辑 docs/novel-pillars.md 与各章大纲")
        return 0
