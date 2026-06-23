"""init-project command — creator / studio scaffold."""
from pathlib import Path

from infra.cli.options import InitProjectOptions
from infra.creator_mode import (
    CREATION_MODE_ADVANCE,
    CREATION_MODE_COMPANION,
    CREATION_MODE_STUDIO,
)
from infra.project_init import init_minimal_short_project

from .base import Command


class InitProjectCommand(Command):
    name = "init-project"
    description = "新建创作者 / 工作室项目脚手架"

    def execute(self, options: InitProjectOptions) -> int:
        out = Path(options.out).resolve() if options.out else None
        try:
            result = init_minimal_short_project(
                slug=options.slug,
                title=options.title,
                protagonist=options.protagonist,
                genre=options.genre,
                chapter_count=options.chapters,
                creation_mode=options.creation_mode,
                out_dir=out,
                overwrite=options.overwrite,
            )
        except (ValueError, FileExistsError) as exc:
            print(f"[错误] {exc}")
            return 1

        print("=" * 60)
        print(f"项目已创建: {result.title} ({result.slug})")
        print("=" * 60)
        print(f"  模式: {result.creation_mode}")
        print(f"  路径: {result.root}")
        print(f"  章节: {result.chapter_count} 章大纲")
        print(f"  文件: {len(result.files_written)} 个")
        print()
        print("下一步:")
        print(f"  export LINGWEN_PROJECT_ROOT={result.root}")
        if result.creation_mode == CREATION_MODE_COMPANION:
            print("  bash scripts/run-companion-check.sh")
            print()
            print("  # 人主笔写正文；需要机写时再开 preflight/batch")
        elif result.creation_mode == CREATION_MODE_ADVANCE:
            print("  export LINGWEN_PRODUCTION_MODE=canon")
            print("  export LINGWEN_REAL_LLM=1")
            end = min(10, result.chapter_count)
            print(f"  bash scripts/run-advance-volume.sh 1 {end} {end} 0.30")
            print()
            print("  # 先编辑全局大纲中的卷纲表，再 batch")
        else:
            print("  export LINGWEN_PRODUCTION_MODE=canon")
            print("  export LINGWEN_REAL_LLM=1")
            print("  python -m infra.agent_system.chapter_production_pilot \\")
            print("    --preflight-only --chapter-num 1")
            print()
            print("  # 生产前请编辑 docs/novel-pillars.md 与各章大纲")
        print()
        print("  文档: novel-factory/docs/creator-onboarding.md")
        return 0
