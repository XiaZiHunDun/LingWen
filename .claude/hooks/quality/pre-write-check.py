#!/usr/bin/env python3
"""
PreToolUse Hook: 检测章节文件是否包含质量问题
在写入/编辑章节前进行初步检测

触发条件: Write/Edit 工具作用于 03_内容仓库/**/*.md 文件
"""

import json
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_chapter_content_from_input() -> tuple:
    """从stdin读取工具输入"""
    try:
        data = json.load(sys.stdin)
        return data.get("tool_input", {})
    except json.JSONDecodeError:
        return {}


# 加载规则
SCIFI_TERMS = [
    "核废土", "辐射区", "辐射污染", "放射性污染", "核辐射",
    "核武器", "核弹", "核爆", "核爆炸", "核打击",
    "基因变异", "基因突变", "变异生物", "变异兽",
    "能量护盾", "激光武器", "激光", "等离子", "导弹",
    "飞船", "战舰", "航空母舰", "飞机",
    "人工智能", "量子", "纳米", "电子设备",
    "全息投影", "全息", "通讯信号",
    "基因治疗", "纳米医疗", "医疗舱",
    "防护服", "太空服", "作战服",
    "雷达扫描", "生命探测仪", "热成像",
    "核动力", "能量核心", "电池",
]

AI_PATTERNS = [
    "首先", "其次", "最后",
    "那一刻", "突然", "霎时", "刹那",
    "可以看出", "值得注意的是", "实际上", "显然", "明显地", "显而易见",
    "因此", "所以", "由于", "于是乎", "紧接着",
    "不断地", "持续地",
]

# Phase 3: 新检测模式
PACING_PATTERNS = [
    "战斗", "攻击", "冲击", "爆发", "厮杀", "搏斗",
    "对决", "交锋", "对抗",
]

SCENE_ABRUPT_PATTERNS = [
    "忽然", "突然", "下一秒", "刹那间", "瞬间", "眨眼间",
]

DIALOGUE_FORMAL_PATTERNS = [
    "我相信", "毫无疑问", "必须承认", "从某种意义上", "事实上",
    "总的来说", "不言而喻", "显而易见", "众所周知",
]


def check_content(content: str) -> dict:
    """检测内容中的质量问题"""
    issues = {"worldview": [], "ai_trace": [], "pacing": [], "scene": [], "dialogue": []}

    for term in SCIFI_TERMS:
        if term in content:
            count = content.count(term)
            issues["worldview"].append(f"{term}({count}处)")

    for pattern in AI_PATTERNS:
        if pattern in content:
            count = content.count(pattern)
            issues["ai_trace"].append(f"{pattern}({count}处)")

    # Phase 3: 新检测
    for pattern in PACING_PATTERNS:
        if pattern in content:
            count = content.count(pattern)
            issues["pacing"].append(f"{pattern}({count}处)")

    for pattern in SCENE_ABRUPT_PATTERNS:
        if pattern in content:
            count = content.count(pattern)
            issues["scene"].append(f"{pattern}({count}处)")

    for pattern in DIALOGUE_FORMAL_PATTERNS:
        if pattern in content:
            count = content.count(pattern)
            issues["dialogue"].append(f"{pattern}({count}处)")

    return issues


def main():
    """从stdin读取工具输入，检测质量问题"""
    try:
        input_data = get_chapter_content_from_input()
        if not input_data:
            print(json.dumps({"allowed": True}))
            return

        tool_input = input_data

        # 获取文件路径
        file_path = tool_input.get("file_path", "")

        # 只检测 03_内容仓库 目录下的 md 文件
        if not file_path.endswith(".md") or "03_内容仓库" not in file_path:
            print(json.dumps({"allowed": True}))
            return

        # 获取内容
        content = tool_input.get("content", "")

        if not content:
            print(json.dumps({"allowed": True}))
            return

        # 检测问题
        issues = check_content(content)

        # 汇总问题数量
        total_issues = len(issues["worldview"]) + len(issues["ai_trace"]) + len(issues["pacing"]) + len(issues["scene"]) + len(issues["dialogue"])

        if total_issues > 0:
            warnings = []
            if issues["worldview"]:
                warnings.append(f"世界观: {', '.join(issues['worldview'][:5])}")
            if issues["ai_trace"]:
                warnings.append(f"AI痕迹: {', '.join(issues['ai_trace'][:5])}")
            if issues["pacing"]:
                warnings.append(f"节奏: {', '.join(issues['pacing'][:5])}")
            if issues["scene"]:
                warnings.append(f"场景: {', '.join(issues['scene'][:5])}")
            if issues["dialogue"]:
                warnings.append(f"对话: {', '.join(issues['dialogue'][:5])}")

            warning_msg = f"[Hook警告] 检测到{total_issues}处质量问题: {'; '.join(warnings)}"

            # 输出警告但不阻止
            print(json.dumps({
                "allowed": True,
                "warnings": [warning_msg]
            }))
        else:
            print(json.dumps({"allowed": True}))

    except Exception:
        # 出错时允许通过，避免阻塞工作
        print(json.dumps({"allowed": True}))


if __name__ == "__main__":
    main()
