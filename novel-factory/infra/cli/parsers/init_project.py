"""init-project subparser — scaffold creator / studio project."""
import argparse

from infra.creator_mode import CREATION_MODES


def add_init_project_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    return subparsers.add_parser(
        "init-project",
        help="新建创作者 / 工作室项目脚手架",
        description="在 projects/<slug>/ 生成分章大纲、配置与支柱",
    )


def register_init_project_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("slug", help="项目标识（小写、连字符），如 anye-xinbiao")
    parser.add_argument("--title", required=True, help="书名，如 暗夜信标")
    parser.add_argument("--protagonist", default="沈柯", help="主角名（默认：沈柯）")
    parser.add_argument("--genre", default="科幻悬疑", help="类型（默认：科幻悬疑）")
    parser.add_argument(
        "--creation-mode",
        choices=sorted(CREATION_MODES),
        default="companion",
        help="companion=陪伴 | advance=推进 | studio=工厂样章（默认 companion）",
    )
    parser.add_argument(
        "--chapters",
        type=int,
        default=10,
        help="章数上限/大纲数（companion 1–30，advance 1–360，studio 固定 10）",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="输出目录（默认：novel-factory/projects/<slug>）",
    )
    parser.add_argument("--overwrite", action="store_true", help="目录已存在时覆盖写入")
