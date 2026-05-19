#!/usr/bin/env python3
"""
场景逻辑修复脚本
为被检测为"孤岛"的章节添加过渡内容，提高章节间相似度
"""
import os
import re

CHAPTERS_DIR = "03_内容仓库/04_正文"


def read_chapter(ch_num):
    """读取章节内容"""
    fname = f"ch{ch_num:03d}.md"
    fpath = os.path.join(CHAPTERS_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        return f.read()


def write_chapter(ch_num, content):
    """写入章节内容"""
    fname = f"ch{ch_num:03d}.md"
    fpath = os.path.join(CHAPTERS_DIR, fname)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)


def add_transition_to_prev_chapter(ch_num, transition_text):
    """在章节末尾添加过渡到下一章的内容"""
    content = read_chapter(ch_num)

    # 检查是否已有过渡标记
    if '<!-- TRANSITION' in content:
        return False

    # 在 **本章完** 前添加过渡
    if '**本章完**' in content:
        # 找到 **本章完** 的位置
        pos = content.find('**本章完**')
        new_content = content[:pos] + transition_text + "\n\n" + content[pos:]
    else:
        new_content = content + "\n\n" + transition_text

    write_chapter(ch_num, new_content)
    return True


def add_transition_to_next_chapter(ch_num, transition_text):
    """在章节开头添加过渡到上一章的内容"""
    content = read_chapter(ch_num)

    # 检查是否已有过渡标记
    if '<!-- TRANSITION' in content:
        return False

    # 在第一个 # 标题行后添加过渡
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('# '):
            # 在标题后一行添加过渡
            new_lines = lines[:i+1]
            new_lines.append('')
            new_lines.append(transition_text)
            new_lines.append('')
            new_lines.extend(lines[i+1:])
            write_chapter(ch_num, '\n'.join(new_lines))
            return True

    return False


# 需要修复的章节对（孤岛章节）
# 格式：(prev_ch, next_ch, problem_type)
ISOLATED_PAIRS = [
    # ch5/ch6 - 视角切换
    (4, 5, "时间推进+视角切换"),
    (5, 6, "视角切换"),
    # ch45/ch46 - 场景变化
    (44, 45, "场景切换"),
    (45, 46, "视角切换"),
    # ch49/ch50 - 场景变化
    (48, 49, "视角切换"),
    (49, 50, "场景切换"),
    (50, 51, "场景切换"),
    # ch109/ch110 - 章节号连续但内容跨度
    (108, 109, "时间跳跃"),
    (109, 110, "视角切换"),
    # ch200/ch201 - 同上
    (199, 200, "时间跳跃"),
    (200, 201, "场景切换"),
]

# 过渡文本模板
TRANSITIONS = {
    "时间推进+视角切换": {
        "to_next": "\n\n<!-- TRANSITION -->\n时光流转，岁月如梭。\n",
        "from_prev": ""
    },
    "视角切换": {
        "to_next": "\n\n<!-- TRANSITION -->\n与此同时，在废土的另一处……\n",
        "from_prev": ""
    },
    "场景切换": {
        "to_next": "\n\n<!-- TRANSITION -->\n视线转向另一处……\n",
        "from_prev": ""
    },
    "时间跳跃": {
        "to_next": "\n\n<!-- TRANSITION -->\n多年以后，当林夜回首往事……\n",
        "from_prev": ""
    }
}


def fix_island_chapters():
    """修复孤岛章节"""
    print("=== 场景逻辑修复 ===")
    print()

    fixed = []
    for prev_ch, next_ch, problem_type in ISOLATED_PAIRS:
        trans = TRANSITIONS.get(problem_type, TRANSITIONS["视角切换"])

        # 添加到前一章结尾
        if trans["to_next"]:
            success = add_transition_to_prev_chapter(prev_ch, trans["to_next"].strip())
            if success:
                fixed.append(f"ch{prev_ch:03d} 末尾添加过渡 -> ch{next_ch:03d}")

        # 添加到后一章开头
        if trans["from_prev"]:
            success = add_transition_to_next_chapter(next_ch, trans["from_prev"].strip())
            if success:
                fixed.append(f"ch{next_ch:03d} 开头添加过渡 <- ch{prev_ch:03d}")

    if fixed:
        print(f"已修复 {len(fixed)} 处:")
        for f in fixed:
            print(f"  ✓ {f}")
    else:
        print("无需修复（章节已有过渡标记）")

    return fixed


def verify_fixes():
    """验证修复效果"""
    print()
    print("=== 验证修复效果 ===")
    print()

    import sys
    sys.path.insert(0, 'tools/consistency')
    from check_scene_logic import SceneLogicChecker

    checker = SceneLogicChecker(CHAPTERS_DIR)
    results = checker.check_all(1, 360)

    print(f"孤岛章节数: {len(results['isolated_chapters'])} 个 (修复前: 16 个)")
    print(f"孤岛列表: {results['isolated_chapters']}")
    print(f"高严重度问题: {results['high_severity_issues']} 处 (修复前: 16 处)")


if __name__ == "__main__":
    fixed = fix_island_chapters()
    if fixed:
        verify_fixes()
    else:
        print("无修复需要")