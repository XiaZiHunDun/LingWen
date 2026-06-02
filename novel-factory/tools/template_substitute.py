#!/usr/bin/env python3
"""模板占位符替换工具 - 替代 sed -i "s/{KEY}/value/g"

用法 (Python API):
    from tools.template_substitute import substitute
    substitute(Path("file.yaml"), {"{PROJECT_NAME}": "星陨纪元", "{DATE}": "2026-06-02"})

用法 (CLI):
    python tools/template_substitute.py file.yaml --set '{PROJECT_NAME}=星陨纪元' --set '{DATE}=2026-06-02'

Why:
    - 避免 sed 在不同 OS（macOS/Linux）上的 -i 行为差异
    - 不需要手动转义 / & 等正则特殊字符
    - 可被 Python 单测覆盖（bash + sed 难测试）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Mapping, Union

PathLike = Union[str, Path]


def substitute(file_path: PathLike, mapping: Mapping[str, str]) -> int:
    """原地替换文件中的占位符。

    Args:
        file_path: 目标文件路径
        mapping: 占位符 -> 替换值。键的写法应与文件中出现的一致（建议带花括号）。

    Returns:
        实际发生替换的次数（基于 plain str.replace 的累计计数）。
    """
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    total = 0
    for placeholder, value in mapping.items():
        if not placeholder:
            continue
        count = content.count(placeholder)
        if count:
            content = content.replace(placeholder, value)
            total += count
    if total:
        path.write_text(content, encoding="utf-8")
    return total


def _parse_kv(pairs: list[str]) -> Dict[str, str]:
    """解析 --set key=value 形式的列表"""
    out: Dict[str, str] = {}
    for raw in pairs or []:
        if "=" not in raw:
            raise ValueError(f"--set 格式错误：{raw}（应为 key=value）")
        k, _, v = raw.partition("=")
        out[k] = v
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="原地替换文件中的占位符（替代 sed -i）")
    parser.add_argument("file", help="目标文件")
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="占位符替换规则（可多次）",
    )
    args = parser.parse_args(argv)

    mapping = _parse_kv(args.set)
    if not mapping:
        print("ERROR: 至少需要一个 --set KEY=VALUE", file=sys.stderr)
        return 1

    n = substitute(args.file, mapping)
    print(f"{args.file}: {n} 处替换")
    return 0


if __name__ == "__main__":
    sys.exit(main())
