#!/usr/bin/env python3
"""
PostToolUse Hook: 章节文件自动修复
在写入章节后自动进行规则修复

触发条件: Write 工具作用于 03_内容仓库/**/*.md 文件
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def extract_chapter_num(file_path: str) -> int:
    """从文件路径提取章节号"""
    match = re.search(r'ch(\d+)\.md$', file_path)
    if match:
        return int(match.group(1))
    return 0


def repair_chapter(chapter_num: int, dry_run: bool = True) -> dict:
    """
    修复指定章节

    Args:
        chapter_num: 章节编号
        dry_run: 是否干跑

    Returns:
        修复结果
    """
    results = {}

    # 修复世界观
    cmd = [
        "python", "-c",
        f"""
import sys
sys.path.insert(0, '{PROJECT_ROOT}')
from infra.quality import WorldviewRepairer
repairer = WorldviewRepairer()
result = repairer.repair({chapter_num})
print(f'worldview:{{result.changes}}')
"""
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
        results["worldview"] = int(output.strip().split(":")[-1])
    except:
        results["worldview"] = 0

    # 修复AI痕迹
    cmd = [
        "python", "-c",
        f"""
import sys
sys.path.insert(0, '{PROJECT_ROOT}')
from infra.quality import AITraceRepairer
repairer = AITraceRepairer()
result = repairer.repair({chapter_num})
print(f'ai_trace:{{result.changes}}')
"""
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
        results["ai_trace"] = int(output.strip().split(":")[-1])
    except:
        results["ai_trace"] = 0

    return results


def main():
    """从环境变量获取写入的文件路径，执行自动修复"""
    try:
        # 获取写入的文件路径（通过环境变量传递）
        file_path = os.environ.get("CLAUDE_HOOK_FILE_PATH", "")

        if not file_path or "03_内容仓库" not in file_path or not file_path.endswith(".md"):
            print(json.dumps({"allowed": True}))
            return

        # 提取章节号
        chapter_num = extract_chapter_num(file_path)
        if chapter_num == 0:
            print(json.dumps({"allowed": True}))
            return

        # 执行修复（干跑模式，不实际写入）
        results = repair_chapter(chapter_num, dry_run=True)

        total_changes = results.get("worldview", 0) + results.get("ai_trace", 0)

        if total_changes > 0:
            messages = []
            if results.get("worldview", 0) > 0:
                messages.append(f"世界观替换{results['worldview']}处")
            if results.get("ai_trace", 0) > 0:
                messages.append(f"AI痕迹替换{results['ai_trace']}处")

            print(json.dumps({
                "allowed": True,
                "messages": [f"[Hook] ch{chapter_num:03d}: {', '.join(messages)}"]
            }))
        else:
            print(json.dumps({"allowed": True}))

    except Exception as e:
        print(json.dumps({"allowed": True}))


if __name__ == "__main__":
    main()