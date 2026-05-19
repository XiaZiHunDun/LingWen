#!/usr/bin/env python3
"""
场景逻辑修复脚本 v2
为被检测为"孤岛"的章节添加过渡内容，提高章节间相似度

改进：使用叙事性的过渡文本，而非通用的标记文本
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


def add_transition(ch_num, transition_text, position="end"):
    """
    添加过渡内容

    Args:
        ch_num: 章节号
        transition_text: 过渡文本
        position: 'end' = 在本章完前添加, 'start' = 在章节开头添加
    """
    content = read_chapter(ch_num)

    # 检查是否已有此过渡标记
    marker = f"<!-- TRANSITION TO {ch_num + 1} -->"
    if marker in content:
        return False

    if position == "end":
        if '**本章完**' in content:
            pos = content.find('**本章完**')
            new_content = content[:pos] + transition_text + "\n\n" + content[pos:]
        else:
            new_content = content + "\n\n" + transition_text
    else:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('# '):
                new_lines = lines[:i+1]
                new_lines.append('')
                new_lines.append(transition_text)
                new_lines.append('')
                new_lines.extend(lines[i+1:])
                new_content = '\n'.join(new_lines)
                break
        else:
            return False

    write_chapter(ch_num, new_content)
    return True


def remove_transitions():
    """移除之前添加的过渡（用于重新开始）"""
    for i in range(1, 361):
        content = read_chapter(i)
        if '<!-- TRANSITION' in content:
            # 移除所有 TRANSITION 标记的段落
            lines = content.split('\n')
            new_lines = []
            skip = False
            for line in lines:
                if '<!-- TRANSITION' in line:
                    skip = True
                    continue
                if skip and line.strip() == '':
                    continue
                if skip and not line.startswith('#'):
                    skip = False
                if not skip:
                    new_lines.append(line)
            write_chapter(i, '\n'.join(new_lines))


# 针对性的过渡文本（根据具体章节内容设计）
TARGETED_TRANSITIONS = {
    # ch4 -> ch5: 林夜成长为复仇者 -> 继续成长
    (4, 5): {
        "text": "但林夜没有停下脚步。他知道，这只是开始。\n\n复仇的路还很长，而他已经踏上了这条路。",
        "position": "end"
    },
    # ch5 -> ch6: 林夜视角 -> 苏琳视角（视角切换）
    (5, 6): {
        "text": "---\n\n与此同时，在废土的另一个角落——",
        "position": "end"
    },
    # ch44 -> ch45: 林夜苏琳星空夜谈 -> 继续星空场景
    (44, 45): {
        "text": "那一夜的星空，成为他们记忆中永不磨灭的光芒。",
        "position": "end"
    },
    # ch45 -> ch46: 星空 -> 山洞莫言（场景切换）
    (45, 46): {
        "text": "---\n\n与此同时，在废土深处的某个山洞里——",
        "position": "end"
    },
    # ch48 -> ch49: 铁蛋照顾莫言 -> 莫言剑断
    (48, 49): {
        "text": "铁蛋的笨拙守护，悄然改变着什么。\n\n但有些东西，终究无法挽回——",
        "position": "end"
    },
    # ch49 -> ch50: 莫言修剑 -> 莫言噩梦
    (49, 50): {
        "text": "那个夜晚过去了，但噩梦从未停止。",
        "position": "end"
    },
    # ch50 -> ch51: 莫言噩梦 -> 继续莫言线
    (50, 51): {
        "text": "黎明的光穿透山洞，照在莫言苍白的脸上。",
        "position": "end"
    },
    # ch108 -> ch109: 直面暗皇 -> 决战开始
    (108, 109): {
        "text": "暗皇的威胁迫在眉睫，但守护者们已经做好了准备。\n\n决战，开始了。",
        "position": "end"
    },
    # ch109 -> ch110: 决战开始 -> 守护的意义
    (109, 110): {
        "text": "在战火中，他们更加深刻地理解了守护的意义。",
        "position": "end"
    },
    # ch199 -> ch200: 彼岸 -> 决战前夜
    (199, 200): {
        "text": "新宇宙已经诞生，但最终的对决还在前方。",
        "position": "end"
    },
    # ch200 -> ch201: 决战前夜 -> 宇宙奇点（场景变化）
    (200, 201): {
        "text": "告别了新宇宙的诞生，林夜和苏琳踏上了新的征程——\n\n五大宇宙奇点的召唤，正在传来。",
        "position": "end"
    },
}


def apply_targeted_fixes():
    """应用针对性的修复"""
    print("=== 场景逻辑修复 v2 ===")
    print()

    fixed = []
    for (prev_ch, next_ch), config in TARGETED_TRANSITIONS.items():
        text = config["text"]
        position = config["position"]

        success = add_transition(prev_ch, text, position)
        if success:
            fixed.append(f"ch{prev_ch:03d}")
            print(f"  ✓ ch{prev_ch:03d} 添加过渡 -> ch{next_ch:03d}")
            print(f"    文本: {text[:30]}...")

    print()
    print(f"已修复 {len(fixed)} 处")
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

    # 检查修复后的连接度
    for res in results['results']:
        if res['chapter'] in [4, 5, 44, 45, 48, 49, 50, 108, 109, 199, 200]:
            conn = res.get('connections', {})
            print(f"ch{res['chapter']:03d}: prev_conn={conn.get('prev', 0):.2f}, next_conn={conn.get('next', 0):.2f}")

    print()
    print(f"孤岛章节数: {len(results['isolated_chapters'])} 个 (修复前: 16 个)")
    print(f"高严重度问题: {results['high_severity_issues']} 处 (修复前: 16 处)")


if __name__ == "__main__":
    import sys
    if '--reset' in sys.argv:
        print("重置过渡...")
        remove_transitions()
        print("完成")
    else:
        fixed = apply_targeted_fixes()
        if fixed:
            verify_fixes()