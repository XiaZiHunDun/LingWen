#!/usr/bin/env python3
"""
PostToolUse Hook: 章节文件自动检测报告
在写入章节后生成检测报告（供参考）

触发条件: Write 工具作用于 03_内容仓库/**/*.md 文件

注意: 由于Hook环境限制，此脚本生成报告但不自动修复
      如需自动修复，请使用 batch_repair.py 工具
"""

import sys
import json
import re
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def extract_chapter_num(file_path: str) -> int:
    """从文件路径提取章节号"""
    match = re.search(r'ch(\d+)\.md$', file_path)
    if match:
        return int(match.group(1))
    return 0


def check_chapter(chapter_num: int) -> dict:
    """检测章节质量问题"""
    try:
        from infra.quality import WorldviewChecker, AITraceChecker

        worldview_checker = WorldviewChecker()
        ai_trace_checker = AITraceChecker()

        worldview_issues = worldview_checker.check(chapter_num)
        ai_trace_issues = ai_trace_checker.check(chapter_num)

        return {
            "chapter": chapter_num,
            "worldview_count": len(worldview_issues),
            "ai_trace_count": len(ai_trace_issues),
            "total": len(worldview_issues) + len(ai_trace_issues)
        }
    except Exception as e:
        return {"chapter": chapter_num, "error": str(e)}


def main():
    """从stdin读取工具输入，生成检测报告"""
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input", {})

        # 获取文件路径
        file_path = tool_input.get("file_path", "")

        # 只检测 03_内容仓库 目录下的 md 文件
        if not file_path.endswith(".md") or "03_内容仓库" not in file_path:
            print(json.dumps({"allowed": True}))
            return

        # 提取章节号
        chapter_num = extract_chapter_num(file_path)
        if chapter_num == 0:
            print(json.dumps({"allowed": True}))
            return

        # 检测问题
        result = check_chapter(chapter_num)

        if result.get("total", 0) > 0:
            messages = []
            if result.get("worldview_count", 0) > 0:
                messages.append(f"世界观{result['worldview_count']}处")
            if result.get("ai_trace_count", 0) > 0:
                messages.append(f"AI痕迹{result['ai_trace_count']}处")

            print(json.dumps({
                "allowed": True,
                "messages": [f"[Hook检测] ch{chapter_num:03d}: {', '.join(messages)} (详见tools/verify_quality.py)"]
            }))
        else:
            print(json.dumps({"allowed": True}))

    except Exception as e:
        print(json.dumps({"allowed": True}))


if __name__ == "__main__":
    main()