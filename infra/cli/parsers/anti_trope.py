"""anti-trope subparser — generate anti-trope creative options."""
import argparse


def add_anti_trope_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'anti-trope' 子命令的参数解析器。

    用法:
        lingwen.py anti-trope --outline "<outline text>" --count 3
    """
    parser = subparsers.add_parser(
        "anti-trope",
        help="生成反套路创意选项",
        description="在章节大纲生成后、审核前，生成反套路创意选项供选择",
    )
    parser.add_argument(
        "--outline",
        type=str,
        required=True,
        help="章节大纲内容",
    )
    parser.add_argument("--count", type=int, default=3, help="生成数量 (默认: 3)")
    parser.add_argument(
        "--format",
        action="store_true",
        default=True,
        help="格式化输出",
    )
    return parser
