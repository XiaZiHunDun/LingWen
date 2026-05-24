#!/usr/bin/env python3
"""
角色一致性修复脚本 - v9.1
基于 character_profiles.json 修复角色行为/对话不一致问题

修复策略：
1. 读取 character_profiles.json 获取角色设定
2. 对每章进行角色行为检查
3. 使用 MiniMax API 进行深度分析和修复
"""

import json
import sys
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.ai_service import MiniMaxProvider, ProviderConfig


class CharacterConsistencyFixer:
    """角色一致性修复器"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.chapters_dir = PROJECT_ROOT / '03_内容仓库' / '04_正文'
        self.characters = self._load_character_profiles()

        # 初始化AI Provider
        self.provider = None
        if self.api_key:
            config = ProviderConfig(api_key=self.api_key, timeout=120, max_retries=2)
            self.provider = MiniMaxProvider(config)

    def _load_character_profiles(self) -> Dict[str, Any]:
        """加载角色设定档案"""
        profile_path = PROJECT_ROOT / "03_内容仓库" / "角色设定" / "character_profiles.json"
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {c["name"]: c for c in data.get("characters", [])}
        except Exception as e:
            print(f"[WARN] 无法加载角色档案: {e}")
            return {}

    def read_chapter(self, chapter_num: int) -> str:
        """读取章节"""
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        if not ch_file.exists():
            return ""
        content = ch_file.read_text(encoding='utf-8')
        # 移除markdown标题
        lines = content.split('\n')
        if lines and lines[0].startswith('#'):
            lines = lines[1:]
        return '\n'.join(lines).strip()

    def write_chapter(self, chapter_num: int, content: str):
        """写入章节"""
        ch_file = self.chapters_dir / f'ch{chapter_num:03d}.md'
        # 恢复标题
        full_content = f"# 第{chapter_num}章\n\n{content}"
        ch_file.write_text(full_content, encoding='utf-8')

    def _call_llm(self, prompt: str, max_tokens: int = 2000) -> str:
        """调用LLM"""
        if not self.provider:
            return ""
        try:
            return self.provider.generate(prompt=prompt, max_tokens=max_tokens, temperature=0.3)
        except Exception as e:
            print(f"[LLM ERROR] {e}")
            return ""

    def _parse_json(self, response: str) -> Any:
        """解析JSON响应"""
        try:
            text = response.strip()
            if text.startswith("```"):
                parts = text.split("```")
                if len(parts) >= 2:
                    text = parts[1]
                    if text.startswith("json"):
                        text = text[4:].lstrip("\n")
            return json.loads(text.strip())
        except:
            return {}

    def analyze_character_issues(self, chapter_num: int, content: str) -> List[Dict]:
        """分析章节中的角色问题"""
        if not self.characters:
            return []

        prompt = f'''检查以下章节中的角色行为是否符合人设。返回JSON格式：

角色设定：
{json.dumps(list(self.characters.values())[:5], ensure_ascii=False, indent=2)[:3000]}

章节内容：
{content[:4000]}

对于每个发现的角色不一致问题，返回JSON数组格式：
[{{"character": "角色名", "issue_type": "问题类型", "location": "位置", "original": "原文", "suggested": "建议修改"}}, ...]

如果没有发现问题，返回空数组：[]

只返回JSON，不要其他内容。'''

        response = self._call_llm(prompt)
        if not response:
            return []

        data = self._parse_json(response)
        return data if isinstance(data, list) else []

    def fix_chapter(self, chapter_num: int, issues: List[Dict]) -> str:
        """基于问题列表修复章节"""
        if not issues:
            return self.read_chapter(chapter_num)

        content = self.read_chapter(chapter_num)

        prompt = f'''请修复以下章节中的角色一致性问题。

角色设定档案：
{json.dumps(list(self.characters.values())[:5], ensure_ascii=False, indent=2)[:2000]}

需要修复的问题：
{json.dumps(issues, ensure_ascii=False, indent=2)[:2000]}

章节原文：
{content[:5000]}

请直接输出修复后的章节正文，只包含修改后的内容，不要有解释或标记。
确保：
1. 角色行为符合其性格设定
2. 对话风格符合角色背景
3. 能力使用与设定等级匹配
4. 保持原文的剧情和情感

只返回JSON格式的修复后内容：
{{"content": "修复后的正文"}}
'''

        response = self._call_llm(prompt, max_tokens=4000)
        if not response:
            return content

        data = self._parse_json(response)
        if isinstance(data, dict) and "content" in data:
            return data["content"]

        return content

    def process_chapters(self, chapter_nums: List[int], dry_run: bool = False) -> Dict[int, int]:
        """
        批量处理章节

        Returns:
            {chapter_num: issue_count}
        """
        results = {}
        total_issues = 0

        for ch_num in chapter_nums:
            content = self.read_chapter(ch_num)
            if not content:
                print(f"ch{ch_num:03d}: 文件不存在，跳过")
                results[ch_num] = 0
                continue

            # 分析问题
            issues = self.analyze_character_issues(ch_num, content)
            issue_count = len(issues) if isinstance(issues, list) else 0

            if issue_count > 0:
                print(f"ch{ch_num:03d}: 发现 {issue_count} 个角色问题")
                total_issues += issue_count

                if not dry_run:
                    # 修复
                    fixed_content = self.fix_chapter(ch_num, issues)
                    self.write_chapter(ch_num, fixed_content)
                    print(f"ch{ch_num:03d}: ✓ 已修复")
            else:
                print(f"ch{ch_num:03d}: ✓ 无问题")

            results[ch_num] = issue_count

        print(f"\n总计: 发现 {total_issues} 个角色问题")
        return results


def main():
    import argparse
    import os
    parser = argparse.ArgumentParser(description='角色一致性修复工具')
    parser.add_argument('--chapters', type=str, default='1-120',
                        help='章节范围')
    parser.add_argument('--dry-run', action='store_true',
                        help='只分析不修复')
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
    print(f"模式: {'分析模式(dry-run)' if args.dry_run else '实际修复'}")
    print("-" * 50)

    fixer = CharacterConsistencyFixer()
    results = fixer.process_chapters(chapters, dry_run=args.dry_run)

    modified = sum(1 for v in results.values() if v > 0)
    print("-" * 50)
    print(f"完成: {modified}/{len(chapters)} 个章节有问题需要修复")


if __name__ == '__main__':
    main()