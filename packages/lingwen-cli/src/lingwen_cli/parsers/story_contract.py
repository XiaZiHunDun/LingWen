"""story-contract subparser — generate story contract with anti-trope constraints."""
import argparse


def add_story_contract_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """注册 'story-contract' 子命令的参数解析器。

    用法:
        lingwen.py story-contract "修仙少年逆袭" --genre 玄幻
        lingwen.py story-contract --chapter 42 --persist
    """
    parser = subparsers.add_parser(
        "story-contract",
        help="生成故事合约",
        description="根据题材和查询生成故事合约，包含反套路约束",
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="查询文本，用于题材路由 (默认: 空字符串)",
    )
    parser.add_argument(
        "--genre",
        type=str,
        help="指定题材 (如: 都市, 玄幻)",
    )
    parser.add_argument(
        "--chapter",
        type=int,
        help="章节号，用于生成章节级合约",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="持久化合约到 .story-system/ 目录",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    return parser
