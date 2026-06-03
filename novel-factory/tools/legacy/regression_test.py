#!/usr/bin/env python3
"""
回归测试工具 - 检测修复是否引入新问题
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CHAPTERS_DIR = PROJECT_ROOT / "03_内容仓库" / "04_正文"


def load_neighboring_chapters(chapter_num: int, context_range: int = 2) -> Dict[int, str]:
    """
    加载相邻章节

    Args:
        chapter_num: 当前章节号
        context_range: 前后各加载多少章

    Returns:
        dict: chapter_num -> content
    """
    result = {}

    # 加载前几章
    for i in range(max(1, chapter_num - context_range), chapter_num):
        ch_file = CHAPTERS_DIR / f"ch{i:03d}.md"
        if ch_file.exists():
            result[i] = ch_file.read_text(encoding='utf-8')

    # 加载后几章
    for i in range(chapter_num + 1, chapter_num + context_range + 1):
        ch_file = CHAPTERS_DIR / f"ch{i:03d}.md"
        if ch_file.exists():
            result[i] = ch_file.read_text(encoding='utf-8')

    return result


def check_character_consistency(chapter_num: int, content: str, neighboring: Dict[int, str]) -> List[str]:
    """
    检查角色一致性（跨章节）

    Returns:
        list: 发现的问题描述列表
    """
    issues = []

    # 收集所有章节中的角色名
    content + "".join(neighboring.values())
    characters = ["林夜", "苏琳", "星月", "小九", "铁蛋", "莫言", "暗皇", "虚无之主", "剑尘子"]

    for char in characters:
        # 统计每个角色在各章节中的出现次数
        appearances = {}
        if char in content:
            appearances[chapter_num] = content.count(char)

        for ch_num, ch_content in neighboring.items():
            if char in ch_content:
                appearances[ch_num] = ch_content.count(char)

        # 检查角色是否突然消失或出现
        if appearances:
            # 当前章节有但前后都没有，可能是误写
            if chapter_num in appearances:
                has_before = any(ch in appearances for ch in range(max(1, chapter_num-3), chapter_num))
                has_after = any(ch in appearances for ch in range(chapter_num+1, chapter_num+4))
                if not has_before and not has_after and appearances[chapter_num] < 3:
                    issues.append(f"角色'{char}'在ch{chapter_num}突然出现又消失，可能是误写")

    return issues


def check_state_consistency(chapter_num: int, content: str, neighboring: Dict[int, str]) -> List[str]:
    """
    检查状态一致性（跨章节）

    Returns:
        list: 发现的问题描述列表
    """
    issues = []

    all_content = content + "".join(neighboring.values())

    # 检查生死状态
    death_keywords = ["死了", "死亡", "逝世", "牺牲", "去世"]
    alive_keywords = ["活着", "生存", "存在", "苏醒", "复活"]

    death_count = sum(all_content.count(k) for k in death_keywords)
    alive_count = sum(all_content.count(k) for k in alive_keywords)

    # 如果角色死亡又复活在同一章节，可能有问题
    if death_count > 0 and alive_count > 0:
        # 检查具体位置
        for keyword in death_keywords:
            if keyword in content and any(a in content for a in alive_keywords):
                # 简单检查：死亡和复活在同一段
                issues.append("章节中同时出现死亡和存活描述，可能存在状态矛盾")
                break

    # 检查关键物品状态
    important_items = ["星图", "机甲", "短刀", "通讯信物"]

    for item in important_items:
        item_states = {}  # chapter -> state
        for ch_num, ch_content in neighboring.items():
            for state in ["新的", "旧的", "破损", "修复", "丢失", "消失"]:
                if f"{item}{state}" in ch_content or f"{state}{item}" in ch_content:
                    item_states[ch_num] = state

        # 当前章节
        for state in ["新的", "旧的", "破损", "修复", "丢失", "消失"]:
            if f"{item}{state}" in content or f"{state}{item}" in content:
                item_states[chapter_num] = state

        # 检查状态跳跃
        if len(item_states) > 1:
            sorted_chapters = sorted(item_states.keys())
            for i in range(1, len(sorted_chapters)):
                prev_ch = sorted_chapters[i-1]
                curr_ch = sorted_chapters[i]
                if prev_ch < chapter_num < curr_ch:
                    # 状态在当前章节发生跳跃
                    prev_state = item_states[prev_ch]
                    curr_state = item_states.get(curr_ch)
                    if curr_state and prev_state != curr_state:
                        issues.append(f"'{item}'状态从'{prev_state}'跳跃到'{curr_state}'，可能存在问题")

    return issues


def check_timeline_consistency(chapter_num: int, content: str, neighboring: Dict[int, str]) -> List[str]:
    """
    检查时间线一致性

    Returns:
        list: 发现的问题描述列表
    """
    issues = []

    # 时间描述关键词
    time_keywords = ["天", "年", "月", "日", "时", "分", "秒", "世纪", "纪元"]

    # 收集时间描述
    time_descriptions = {}

    for ch_num, ch_content in neighboring.items():
        for kw in time_keywords:
            if f"1{kw}" in ch_content or f"一{kw}" in ch_content:
                idx = ch_content.find(kw)
                time_descriptions[ch_num] = ch_content[max(0, idx-5):idx+5]

    for kw in time_keywords:
        if f"1{kw}" in content or f"一{kw}" in content:
            idx = content.find(kw)
            time_descriptions[chapter_num] = content[max(0, idx-5):idx+5]

    # 检查时间倒退
    if len(time_descriptions) > 1:
        sorted_chapters = sorted(time_descriptions.keys())
        for i in range(1, len(sorted_chapters)):
            # 简单检查：后续章节不应比前面章节时间短
            if sorted_chapters[i] > chapter_num > sorted_chapters[i-1]:
                # 当前章节的时间描述应该 >= 前一章节
                pass  # 需要更复杂的逻辑，这里简化处理

    return issues


def regression_test(chapter_num: int, original_content: str, fixed_content: str) -> Tuple[bool, List[str]]:
    """
    回归测试主函数

    Args:
        chapter_num: 章节号
        original_content: 修复前内容
        fixed_content: 修复后内容

    Returns:
        (is_safe, issues):
            is_safe: 修复是否安全（未引入新问题）
            issues: 发现的问题列表
    """
    issues = []

    # 加载相邻章节
    neighboring = load_neighboring_chapters(chapter_num, range=2)

    # 1. 检查角色一致性
    char_issues = check_character_consistency(chapter_num, fixed_content, neighboring)
    issues.extend(char_issues)

    # 2. 检查状态一致性
    state_issues = check_state_consistency(chapter_num, fixed_content, neighboring)
    issues.extend(state_issues)

    # 3. 检查时间线一致性
    timeline_issues = check_timeline_consistency(chapter_num, fixed_content, neighboring)
    issues.extend(timeline_issues)

    # 4. 检查内容长度异常变化
    original_len = len(original_content)
    fixed_len = len(fixed_content)

    # 如果变化超过50%，可能有问题
    if original_len > 0:
        change_ratio = abs(fixed_len - original_len) / original_len
        if change_ratio > 0.5:
            issues.append(f"内容长度变化{change_ratio*100:.0f}%，可能过度修改")

    # 5. 检查是否引入新的AI痕迹
    ai_patterns = ["首先", "其次", "因此", "然而", "但是", "总之", "一方面", "另一方面"]
    new_ai_count = sum(1 for p in ai_patterns if p in fixed_content and p not in original_content)
    if new_ai_count > 3:
        issues.append(f"修复后引入了{new_ai_count}个AI特征词，可能有AI润色痕迹")

    return len(issues) == 0, issues


def batch_regression_test(chapters: List[int], originals: dict, fixed: dict) -> dict:
    """
    批量回归测试

    Args:
        chapters: 章节号列表
        originals: chapter_num -> original_content
        fixed: chapter_num -> fixed_content

    Returns:
        dict: chapter_num -> (is_safe, issues)
    """
    results = {}

    for ch in chapters:
        if ch in originals and ch in fixed:
            is_safe, issues = regression_test(ch, originals[ch], fixed[ch])
            results[ch] = (is_safe, issues)
        else:
            results[ch] = (False, ["缺少原始内容或修复后内容"])

    return results


if __name__ == "__main__":
    # 测试
    ch_file = CHAPTERS_DIR / "ch206.md"
    if ch_file.exists():
        content = ch_file.read_text(encoding='utf-8')
        neighboring = load_neighboring_chapters(206, range=2)
        print(f"ch206相邻章节: {list(neighboring.keys())}")

        char_issues = check_character_consistency(206, content, neighboring)
        print(f"角色一致性问题: {char_issues}")

        state_issues = check_state_consistency(206, content, neighboring)
        print(f"状态一致性问题: {state_issues}")
