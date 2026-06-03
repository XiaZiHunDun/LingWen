#!/usr/bin/env python3
"""
章节大纲生成工具
自动为每章生成大纲文件

使用方法:
    python tools/generate_chapter_outlines.py          # 生成所有章节大纲
    python tools/generate_chapter_outlines.py --dry-run # 预览（不写入）
    python tools/generate_chapter_outlines.py --ch 1-30  # 生成指定范围
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class ChapterOutline:
    """章节大纲数据"""
    chapter: int
    title: str
    overview: str
    events: List[str]
    characters: List[str]
    foreshadowing: List[str]
    word_count: int
    perspective: str = "第三人称"
    tension: str = "★★★☆☆"


def extract_chapter_num(filename: str) -> int:
    """从文件名提取章节号"""
    match = re.search(r'ch(\d+)', filename)
    return int(match.group(1)) if match else 0


def extract_title(content: str) -> str:
    """从内容提取章节标题"""
    # 匹配 # 其一章 xxx 或 # 第一章 xxx 格式
    match = re.search(r'^#\s*(其?[一二三四五六七八九十百\d]+章)\s*(.+)', content, re.MULTILINE)
    if match:
        return f"{match.group(1)} {match.group(2).strip()}"
    # 备用匹配
    match = re.search(r'^#\s*(.+)', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "无标题"


def count_words(content: str) -> int:
    """估算字数（中文字符）"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    return chinese_chars


def generate_outline(chapter_num: int, content: str) -> ChapterOutline:
    """
    根据章节内容生成大纲

    Args:
        chapter_num: 章节号
        content: 章节正文

    Returns:
        ChapterOutline对象
    """
    title = extract_title(content)
    word_count = count_words(content)

    # 提取第一段作为概述基础
    paragraphs = content.split('\n\n')
    first_para = ""
    for p in paragraphs:
        p = p.strip()
        if len(p) > 20 and not p.startswith('#'):
            first_para = p[:200]
            break

    # 简单概述生成（后续可升级为LLM分析）
    overview = first_para if first_para else "本章内容概要待补充"

    # 提取人物名（简单的启发式方法）
    characters = extract_main_characters(content)

    # 伏笔检测（关键词匹配）
    foreshadowing = detect_foreshadowing(content)

    # 核心事件（取前3个主要段落）
    events = extract_events(paragraphs)

    # 紧张度评级（基于关键词）
    tension = estimate_tension(content)

    return ChapterOutline(
        chapter=chapter_num,
        title=title,
        overview=overview,
        events=events,
        characters=characters,
        foreshadowing=foreshadowing,
        word_count=word_count,
        perspective="第三人称林夜视角" if "林夜" in content[:500] else "第三人称",
        tension=tension
    )


def extract_main_characters(content: str) -> List[str]:
    """提取主要人物"""
    # 主要角色名单（可扩展）
    main_chars = ["林夜", "苏琳", "星月", "小九", "铁蛋", "莫言", "暗皇", "虚无之主"]
    found = []
    for char in main_chars:
        if char in content[:2000]:  # 只检查前2000字
            found.append(char)
    return found if found else ["待识别"]


def detect_foreshadowing(content: str) -> List[str]:
    """检测伏笔铺设"""
    foreshadow_keywords = [
        "黑暗", "未来", "可能", "预言", "命运",
        "记忆", "血脉", "觉醒", "秘密", "真相",
        "牺牲", "守护", "永恒", "星陨"
    ]
    found = []
    for kw in foreshadow_keywords:
        if kw in content:
            found.append(f"「{kw}」暗示")
    return found[:5] if found else []


def extract_events(paragraphs: List[str]) -> List[str]:
    """提取核心事件"""
    events = []
    seen_sentences = set()

    # 定义事件关键句模式
    event_indicators = [
        "死了", "牺牲", "被杀", "战斗", "追杀",
        "遇见", "相遇", "相救", "发现", "觉醒",
        "决定", "发誓", "承诺", "告别", "离别",
        "突破", "领悟", "融合", "转化"
    ]

    for p in paragraphs:
        p = p.strip()
        if len(p) < 30 or p.startswith('#') or p.startswith('【'):
            continue

        # 分割句子
        sentences = re.split(r'[。！？\.]', p)
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 15 or len(sent) > 100:
                continue

            # 检查是否包含事件指示词
            is_event = any(ind in sent for ind in event_indicators)

            # 或者检查是否为对话（描述动作而非对话）
            has_dialogue = '"' in sent or '"' in sent or '"' in sent

            if is_event or (not has_dialogue and len(sent) > 20):
                # 去重
                if sent not in seen_sentences:
                    seen_sentences.add(sent)
                    if len(sent) > 50:
                        sent = sent[:50] + "..."
                    events.append(f"- {sent}")

        if len(events) >= 4:
            break

    return events if events else ["- 情节内容待补充"]


def estimate_tension(content: str) -> str:
    """估算紧张度"""
    tension_keywords = {
        "紧张": ["战斗", "危机", "追杀", "牺牲", "死亡", "暗域", "觉醒兽"],
        "平缓": ["对话", "回忆", "思考", "相处", "温馨", "新婚"]
    }
    tension_count = sum(content.count(k) for k in tension_keywords["紧张"])
    calm_count = sum(content.count(k) for k in tension_keywords["平缓"])

    if tension_count > calm_count * 2:
        return "★★★★☆"
    elif tension_count > calm_count:
        return "★★★☆☆"
    else:
        return "★★☆☆☆"


def outline_to_markdown(outline: ChapterOutline) -> str:
    """将大纲转换为Markdown格式"""
    lines = [
        f"# {outline.title}",
        "",
        "## 本章概述",
        outline.overview,
        "",
        "## 核心事件",
    ]
    lines.extend(outline.events)
    lines.extend(["", "## 关键人物", "- " + ", ".join(outline.characters)])

    if outline.foreshadowing:
        lines.extend(["", "## 伏笔铺设"])
        for fs in outline.foreshadowing:
            lines.append(f"- {fs}")

    lines.extend([
        "",
        "## 本章数据",
        f"- 字数：~{outline.word_count}",
        f"- 视角：{outline.perspective}",
        f"- 紧张度：{outline.tension}",
    ])

    return '\n'.join(lines)


def process_chapter(chapter_num: int, dry_run: bool = False) -> bool:
    """
    处理单个章节

    Returns:
        是否成功
    """
    chapters_dir = PROJECT_ROOT / "03_内容仓库" / "04_正文"
    ch_file = chapters_dir / f"ch{chapter_num:03d}.md"

    if not ch_file.exists():
        return False

    content = ch_file.read_text(encoding='utf-8')
    if not content.strip():
        return False

    outline = generate_outline(chapter_num, content)
    md_content = outline_to_markdown(outline)

    if not dry_run:
        outline_file = chapters_dir / f"ch{chapter_num:03d}_大纲.md"
        outline_file.write_text(md_content, encoding='utf-8')

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description='章节大纲生成工具')
    parser.add_argument('--chapters', type=str, default='1-360',
                        help='章节范围，如 "1-30" 或 "1,5,10"')
    parser.add_argument('--dry-run', action='store_true',
                        help='只输出不保存')
    parser.add_argument('--limit', type=int, default=None,
                        help='限制处理章节数量')

    args = parser.parse_args()

    # 解析章节范围
    chapters = []
    for part in args.chapters.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            chapters.extend(range(start, end + 1))
        else:
            chapters.append(int(part))

    if args.limit:
        chapters = chapters[:args.limit]

    print(f"待处理章节: {len(chapters)} 个")
    print(f"模式: {'干跑(dry-run)' if args.dry_run else '实际写入'}")
    print("-" * 50)

    success_count = 0
    for ch in chapters:
        if process_chapter(ch, dry_run=args.dry_run):
            success_count += 1
            if not args.dry_run:
                print(f"ch{ch:03d}: ✓ 已生成大纲")
        else:
            print(f"ch{ch:03d}: - 跳过（无内容或文件不存在）")

    print("-" * 50)
    print(f"完成: {success_count}/{len(chapters)} 章")


if __name__ == '__main__':
    main()