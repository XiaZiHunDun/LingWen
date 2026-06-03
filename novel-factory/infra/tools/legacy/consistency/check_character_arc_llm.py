#!/usr/bin/env python3
"""
人物弧光完整性检查器
准备角色弧光分析所需的数据和提示词

这个脚本在Claude Code中运行时，可以直接利用Claude Code的LLM能力
通过标准输入/输出与Claude Code会话交互
"""
import os
import sys
import json
import argparse
from typing import List, Dict, Optional


# 主要角色及其弧光类型配置
CHARACTER_ARCS = {
    '林夜': {
        'arc_type': '成长型',
        'description': '从失去一切到获得力量保护所爱',
        'expected_structure': [
            '失去一切（灾难起点）',
            '获得机遇（觉醒/传承）',
            '艰苦修炼（积累期）',
            '保护所爱（能力验证）',
            '终极抉择（牺牲/胜利）'
        ]
    },
    '苏琳': {
        'arc_type': '陪伴型',
        'description': '与林夜相伴成长，情感深化',
        'expected_structure': [
            '相遇（初始羁绊）',
            '并肩作战（建立信任）',
            '情感深化（确认感情）',
            '共同面对（生死相依）'
        ]
    },
    '小九': {
        'arc_type': '觉醒型',
        'description': '灵宠从初始状态到完全觉醒',
        'expected_structure': [
            '初始状态（灵体/弱化状态）',
            '遇到主人（认主）',
            '能力成长（跟随修炼）',
            '完全觉醒（终极形态/特殊能力）'
        ]
    },
    '星月': {
        'arc_type': '悲剧型',
        'description': '接受命运考验，悲剧或突破',
        'expected_structure': [
            '美好往昔（回忆/起源）',
            '命运转折（悲剧伏笔）',
            '艰难考验（身心折磨）',
            '悲剧结局或突破（牺牲/觉醒）'
        ]
    },
    '暗皇': {
        'arc_type': '反派型',
        'description': '展示威胁到最终对决',
        'expected_structure': [
            '展示力量（确立威胁）',
            '制造危机（升级冲突）',
            '升级冲突（终极对立）',
            '被击败或洗白（结局）'
        ]
    },
}


class CharacterArcChecker:
    """人物弧光检查器"""

    def __init__(self, chapters_dir: str):
        self.chapters_dir = chapters_dir

    def load_chapter(self, chapter_num: int) -> str:
        """加载章节内容"""
        fname = f"ch{chapter_num:03d}.md"
        fpath = os.path.join(self.chapters_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def extract_chapter_content(self, chapter_num: int, content: str) -> str:
        """提取章节正文"""
        lines = content.split('\n')
        body_lines = []
        for i, line in enumerate(lines):
            if i < 2:
                continue
            if '**本章完**' in line:
                break
            body_lines.append(line)
        return '\n'.join(body_lines)

    def get_chapters_for_character(self, character: str, start_ch: int, end_ch: int) -> List[Dict]:
        """收集角色出现的章节"""
        chapters = []
        for ch_num in range(start_ch, end_ch + 1):
            content = self.load_chapter(ch_num)
            if character in content:
                body = self.extract_chapter_content(ch_num, content)
                chapters.append({
                    'chapter': ch_num,
                    'content': body[:1500]
                })
        return chapters

    def build_analysis_prompt(self, character: str, chapters: List[Dict]) -> str:
        """构建分析提示词"""
        arc_info = CHARACTER_ARCS[character]
        combined = '\n\n---\n\n'.join([
            f"=== 第{ch['chapter']}章 ===\n{ch['content']}"
            for ch in chapters
        ])

        arc_type = arc_info['arc_type']
        description = arc_info['description']
        expected = arc_info['expected_structure']

        prompt = f"""你是小说结构分析师。请分析角色"{character}"的弧光完整性。

角色信息:
- 角色名: {character}
- 弧光类型: {arc_type}
- 角色描述: {description}
- 预期弧光阶段: {' → '.join(expected)}

请分析以下章节内容，判断该角色的弧光是否完整：

---

{combined[:10000]}

---

分析要求:
1. 识别该角色在这些章节中的关键事件
2. 判断弧光进展到哪个阶段
3. 指出弧光是否完整，缺失了哪些阶段
4. 如果完整，给出该角色弧光的发展评分(1-10)

请用JSON格式输出：
{{
  "character": "角色名",
  "arc_type": "弧光类型",
  "arc_stage": "当前阶段",
  "is_complete": true/false,
  "missing_stages": ["缺失阶段1", "缺失阶段2"],
  "score": 8,
  "summary": "简要分析说明"
}}

只输出JSON，不要有其他内容。"""
        return prompt

    def build_analysis_task(self, character: str, start_ch: int, end_ch: int) -> Optional[Dict]:
        """构建角色弧光分析任务"""
        if character not in CHARACTER_ARCS:
            return None

        chapters = self.get_chapters_for_character(character, start_ch, end_ch)
        if not chapters:
            return None

        arc_info = CHARACTER_ARCS[character]

        return {
            'character': character,
            'arc_type': arc_info['arc_type'],
            'chapter_range': f"{start_ch}-{end_ch}",
            'chapters_count': len(chapters),
            'prompt': self.build_analysis_prompt(character, chapters)
        }


def main():
    parser = argparse.ArgumentParser(description='人物弧光完整性检查')
    parser.add_argument('chapters_dir', help='章节目录路径')
    parser.add_argument('--start', type=int, default=1, help='起始章节')
    parser.add_argument('--end', type=int, default=50, help='结束章节')
    parser.add_argument('--character', '-c', help='只检查指定角色')
    parser.add_argument('--all', action='store_true', help='检查所有角色')
    parser.add_argument('--output', '-o', help='输出任务JSON文件')
    args = parser.parse_args()

    checker = CharacterArcChecker(args.chapters_dir)
    tasks = []

    if args.character:
        task = checker.build_analysis_task(args.character, args.start, args.end)
        if task:
            tasks.append(task)
        else:
            print(f"错误: 未找到角色'{args.character}'的配置")
            sys.exit(1)
    elif args.all:
        for char in CHARACTER_ARCS:
            task = checker.build_analysis_task(char, args.start, args.end)
            if task:
                tasks.append(task)
    else:
        print("请指定 --character <角色名> 或 --all")
        print(f"可用角色: {', '.join(CHARACTER_ARCS.keys())}")
        sys.exit(1)

    # 输出
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump({'tasks': tasks}, f, ensure_ascii=False, indent=2)
        print(f"任务已保存到: {args.output}")
    else:
        for task in tasks:
            print("=" * 70)
            print(f"角色: {task['character']} ({task['chapters_count']}章)")
            print("=" * 70)
            print(task['prompt'])
            print()


if __name__ == "__main__":
    main()