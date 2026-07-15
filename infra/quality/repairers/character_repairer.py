#!/usr/bin/env python3
"""
角色一致性修复器
基于LLM修复角色行为/对话不一致问题
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.ai_service import MiniMaxProvider, ProviderConfig
from infra.quality import Repairer, RepairResult, YAMLRuleRepairer

logger = logging.getLogger(__name__)


class CharacterConsistencyRepairer(YAMLRuleRepairer):
    """
    角色一致性修复器

    使用YAML规则 + LLM进行角色行为修复
    - 对于规则性修复（已知模式），使用YAML规则
    - 对于复杂修复（需要理解上下文），使用LLM
    """

    def __init__(self, paths=None, api_key: Optional[str] = None):
        super().__init__("character_consistency_rules.yaml", paths)
        self.api_key = api_key or os.getenv('MINIMAX_API_KEY', '')
        self._provider = None
        self._characters: Dict[str, Any] = {}
        self._load_character_profiles()

    @property
    def provider(self) -> Optional[MiniMaxProvider]:
        if self._provider is None and self.api_key:
            config = ProviderConfig(api_key=self.api_key, timeout=120, max_retries=2)
            self._provider = MiniMaxProvider(config)
        return self._provider

    def _load_character_profiles(self):
        """加载角色设定档案"""
        profile_path = self.paths.content_dir / "角色设定" / "character_profiles.json"
        if profile_path.exists():
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._characters = {c["name"]: c for c in data.get("characters", [])}
            except Exception as e:
                logger.warning(f"无法加载角色档案: {e}")

    def _get_rules(self) -> List[Tuple[str, str, str]]:
        """获取规则列表（用于规则性修复）"""
        rules = self._load_rules()
        result = []
        for rule in rules:
            rule_type = rule.get("type", "")
            if rule_type in ("replacement", "character_behavior"):
                source = rule.get("source", "")
                target = rule.get("target", "")
                desc = rule.get("description", "")
                if source and target:
                    result.append((source, target, desc))
        return result

    def _get_llm_prompt(self, chapter_num: int, content: str, issues: List[Dict]) -> str:
        """生成LLM修复提示"""
        characters_json = json.dumps(list(self._characters.values())[:5], ensure_ascii=False, indent=2)
        issues_json = json.dumps(issues, ensure_ascii=False, indent=2)

        return f'''你是小说文字编辑专家。请修复以下章节中的角色一致性问题。

角色设定档案：
{characters_json[:3000]}

需要修复的问题：
{issues_json[:2000]}

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

    def _call_llm(self, prompt: str, max_tokens: int = 4000) -> str:
        """调用LLM"""
        if not self.provider:
            return ""
        try:
            return self.provider.generate(prompt=prompt, max_tokens=max_tokens, temperature=0.3)
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return ""

    def _parse_llm_response(self, response: str) -> Dict:
        """解析LLM的JSON响应"""
        try:
            text = response.strip()
            if text.startswith("```"):
                parts = text.split("```")
                if len(parts) >= 2:
                    text = parts[1]
                    if text.startswith("json"):
                        text = text[4:].lstrip("\n")
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}")
            return {}

    def _analyze_with_llm(self, chapter_num: int, content: str) -> List[Dict]:
        """使用LLM分析章节中的角色问题"""
        if not self._characters or not self.provider:
            return []

        prompt = f'''检查以下章节中的角色行为是否符合人设。返回JSON格式：

角色设定：
{json.dumps(list(self._characters.values())[:5], ensure_ascii=False, indent=2)[:3000]}

章节内容：
{content[:4000]}

对于每个发现的角色不一致问题，返回JSON数组格式：
[{{"character": "角色名", "issue_type": "问题类型", "location": "位置", "original": "原文", "suggested": "建议修改"}}, ...]

如果没有发现问题，返回空数组：[]

只返回JSON，不要其他内容。'''

        response = self._call_llm(prompt)
        if not response:
            return []

        data = self._parse_llm_response(response)
        if isinstance(data, list):
            return data
        return []

    def _apply_llm_fix(self, content: str, issues: List[Dict]) -> str:
        """使用LLM修复内容"""
        if not issues or not self.provider:
            return content

        prompt = self._get_llm_prompt(0, content, issues)
        response = self._call_llm(prompt)

        if not response:
            return content

        data = self._parse_llm_response(response)
        if isinstance(data, dict) and "content" in data:
            return data["content"]

        return content

    def _apply_rules(self, content: str, issues: List) -> Tuple[str, int]:
        """
        应用规则替换

        对于角色一致性修复，优先使用LLM分析+修复，
        规则只用于简单的文本替换
        """
        # 先应用规则性修复
        result, count = super()._apply_rules(content, [])

        # 如果有LLM能力且有角色档案，使用LLM进行深度修复
        if self._characters and self.provider:
            # 分析角色问题
            llm_issues = self._analyze_with_llm(0, result)
            if llm_issues:
                # 使用LLM修复
                fixed = self._apply_llm_fix(result, llm_issues)
                if fixed != result:
                    # 计算实际修改数（简单估算）
                    count += len(llm_issues)
                    result = fixed

        return result, count

    def repair(self, chapter_num: int, issues: List = None) -> RepairResult:
        """
        修复单个章节

        Args:
            chapter_num: 章节编号
            issues: 可选的问题列表（用于针对性修复）

        Returns:
            RepairResult修复结果
        """
        content = self.paths.read_chapter(chapter_num)
        if not content:
            return RepairResult(chapter=chapter_num, success=False, error="章节不存在")

        try:
            # 规则修复
            new_content, rule_changes = self._apply_rules(content, issues or [])

            # LLM深度修复（如有）
            if self._characters and self.provider:
                llm_issues = self._analyze_with_llm(chapter_num, new_content)
                if llm_issues:
                    llm_fixed = self._apply_llm_fix(new_content, llm_issues)
                    if llm_fixed != new_content:
                        new_content = llm_fixed

            changes = self._count_changes(content, new_content)
            if changes > 0:
                self.paths.write_chapter(chapter_num, new_content)

            return RepairResult(
                chapter=chapter_num,
                success=True,
                changes=changes,
                new_content=new_content
            )
        except Exception as e:
            logger.error(f"修复失败 ch{chapter_num:03d}: {e}")
            return RepairResult(chapter=chapter_num, success=False, error=str(e))

    def _count_changes(self, old: str, new: str) -> int:
        """计算修改次数（简化版）"""
        if old == new:
            return 0
        # 简单计算：按行差异估算
        old_lines = set(old.split())
        new_lines = set(new.split())
        return len(new_lines - old_lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='角色一致性修复器')
    parser.add_argument('--chapters', type=str, default='1-10',
                        help='章节范围')
    parser.add_argument('--dry-run', action='store_true',
                        help='只输出不保存')
    parser.add_argument('--limit', type=int, default=None,
                        help='限制处理章节数量')
    parser.add_argument('--api-key', type=str, default=None,
                        help='API密钥（也可通过MINIMAX_API_KEY环境变量）')

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
    print(f"模式: {'干跑(dry-run)' if args.dry_run else '实际修改'}")
    print("-" * 50)

    api_key = args.api_key or os.getenv('MINIMAX_API_KEY', '')
    if not api_key:
        print("[WARN] 未设置API密钥，将只使用规则修复")

    repairer = CharacterConsistencyRepairer(api_key=api_key)

    total_changes = 0
    for ch in chapters:
        result = repairer.repair(ch)
        if result.changes > 0:
            print(f"ch{ch:03d}: ✓ {result.changes} 处修改")
            total_changes += result.changes
        else:
            print(f"ch{ch:03d}: — 无需修改")

    print("-" * 50)
    print(f"完成: 总修改 {total_changes} 处")


if __name__ == '__main__':
    main()
