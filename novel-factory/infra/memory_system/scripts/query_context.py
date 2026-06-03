"""上下文查询脚本

查询记忆系统中的上下文信息，支持多种作用域过滤。

Usage:
    python -m memory_system.scripts.query_context "李逍遥的性格"
    python -m memory_system.scripts.query_context "王宫的描述" --scope chapter
    python -m memory_system.scripts.query_context "李逍遥和赵灵儿的感情" --scope relationship
    python -m memory_system.scripts.query_context "李逍遥" --scope character
    python -m memory_system.scripts.query_context --interactive
"""
import argparse
import sys
from typing import Any, Optional

from infra.memory_system.config import load_yaml
from infra.memory_system.gateway.memory_gateway import MemoryGateway
from infra.memory_system.vector.embedder import Embedder
from infra.memory_system.vector.qdrant_client import QdrantClientWrapper


def load_config() -> dict:
    """加载并验证配置

    Returns:
        配置字典

    Raises:
        RuntimeError: 配置无效
    """
    try:
        config = load_yaml("config/memory_config.yaml")
    except FileNotFoundError as e:
        raise RuntimeError(f"Configuration file not found: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration: {e}")

    required_sections = ["qdrant", "embedding", "storage", "retrieval"]
    for section in required_sections:
        if section not in config:
            raise RuntimeError(f"Missing required config section: {section}")

    return config


def init_gateway(config: dict) -> MemoryGateway:
    """初始化 MemoryGateway

    Args:
        config: 配置字典

    Returns:
        MemoryGateway 实例
    """
    qdrant_wrapper = QdrantClientWrapper()
    embedder = Embedder()

    return MemoryGateway(
        qdrant_wrapper=qdrant_wrapper,
        embedder=embedder,
    )


def format_result(result: dict, index: int) -> str:
    """格式化单个查询结果

    Args:
        result: 查询结果字典
        index: 结果索引

    Returns:
        格式化的字符串
    """
    lines = [
        f"\n{'=' * 60}",
        f"[结果 {index + 1}]"
    ]

    # 基本信息
    if "chapter" in result:
        lines.append(f"章节: {result['chapter']}")
    if "filename" in result:
        lines.append(f"文件: {result['filename']}")
    if "type" in result:
        lines.append(f"类型: {result['type']}")
    if "score" in result:
        lines.append(f"相似度: {result['score']:.4f}")

    # 文本内容
    if "text" in result:
        lines.append(f"\n内容:\n{result['text']}")

    # 其他 payload 数据
    for key, value in result.items():
        if key not in ["text", "chapter", "filename", "type", "score", "vector"]:
            if isinstance(value, str) and len(value) > 200:
                lines.append(f"{key}: {value[:200]}...")
            else:
                lines.append(f"{key}: {value}")

    return "\n".join(lines)


def format_results(results: list[dict], query: str, scope: str) -> str:
    """格式化查询结果列表

    Args:
        results: 结果列表
        query: 查询字符串
        scope: 查询作用域

    Returns:
        格式化的字符串
    """
    lines = [
        "=" * 60,
        f"查询: \"{query}\"",
        f"作用域: {scope}",
        f"结果数量: {len(results)}",
        "=" * 60,
    ]

    if not results:
        lines.append("\n没有找到相关结果。")
        return "\n".join(lines)

    for i, result in enumerate(results):
        lines.append(format_result(result, i))

    return "\n".join(lines)


def interactive_mode(gateway: MemoryGateway) -> int:
    """交互式查询模式

    Args:
        gateway: MemoryGateway 实例

    Returns:
        退出码
    """
    print("\n" + "=" * 60)
    print("记忆系统上下文查询 - 交互模式")
    print("=" * 60)
    print("输入查询内容后按回车搜索")
    print("输入 'scope <type>' 切换作用域 (character/chapter/relationship/all)")
    print("输入 'quit' 或 'exit' 退出")
    print("=" * 60)

    current_scope = "all"

    while True:
        try:
            user_input = input(f"\n[{current_scope}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n退出交互模式。")
            return 0

        if not user_input:
            continue

        # 处理内置命令
        if user_input.lower() in ("quit", "exit", "q"):
            print("退出交互模式。")
            return 0

        if user_input.lower().startswith("scope "):
            new_scope = user_input[6:].strip()
            if new_scope in ("character", "chapter", "relationship", "all"):
                current_scope = new_scope
                print(f"作用域已切换为: {current_scope}")
            else:
                print(f"无效的作用域: {new_scope}")
                print("可选值: character, chapter, relationship, all")
            continue

        # 执行查询
        try:
            results = gateway.query(user_input, scope=current_scope)
            output = format_results(results, user_input, current_scope)
            print(output)
        except Exception as e:
            print(f"查询出错: {e}", file=sys.stderr)
            return 1

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="查询记忆系统中的上下文信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="查询字符串"
    )
    parser.add_argument(
        "--scope",
        "-s",
        choices=["character", "chapter", "relationship", "all"],
        default="all",
        help="查询作用域 (默认: all)"
    )
    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=None,
        help="返回结果数量限制"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="进入交互模式"
    )

    args = parser.parse_args()

    # 交互模式
    if args.interactive:
        config = load_config()
        gateway = init_gateway(config)
        return interactive_mode(gateway)

    # 非交互模式需要 query
    if not args.query:
        parser.print_help()
        print("\n错误: query 是必需参数（除非使用 --interactive）", file=sys.stderr)
        return 1

    # 执行查询
    try:
        config = load_config()
    except RuntimeError as e:
        print(f"配置错误: {e}", file=sys.stderr)
        return 1

    try:
        gateway = init_gateway(config)
    except Exception as e:
        print(f"初始化错误: {e}", file=sys.stderr)
        return 1

    try:
        results = gateway.query(args.query, scope=args.scope, top_k=args.top_k)
        output = format_results(results, args.query, args.scope)
        print(output)
    except Exception as e:
        print(f"查询出错: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
