#!/usr/bin/env python3
"""
修复器基类
所有修复器应继承此类
"""

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.paths import ProjectPaths
from infra.quality.inspector import Issue


@dataclass
class RepairResult:
    """修复结果"""
    chapter: int
    success: bool
    changes: int = 0
    new_content: str = ""
    error: str = ""


class Repairer(ABC):
    """
    修复器抽象基类（R4-005：使用 ABC + abstractmethod 防止直接实例化）

    使用方式:
        class WorldviewRepairer(Repairer):
            def _get_rules(self) -> List[Tuple[str, str]]:
                return [("飞船", "灵舟"), ...]

            def _apply_rule(self, content: str, old: str, new: str) -> str:
                return content.replace(old, new)
    """

    def __init__(self, paths: Optional[ProjectPaths] = None):
        self.paths = paths or ProjectPaths.get()
        self._rules: Optional[List[Tuple[str, str, str]]] = None

    def repair(self, chapter_num: int, issues: List[Issue] = None) -> RepairResult:
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
            new_content, changes = self._apply_rules(content, issues or [])
            if changes > 0:
                self.paths.write_chapter(chapter_num, new_content)

            return RepairResult(
                chapter=chapter_num,
                success=True,
                changes=changes,
                new_content=new_content
            )
        except Exception as e:
            return RepairResult(chapter=chapter_num, success=False, error=str(e))

    def repair_batch(self, chapter_nums: List[int]) -> Dict[int, RepairResult]:
        """
        批量修复章节

        Args:
            chapter_nums: 章节编号列表

        Returns:
            {chapter_num: RepairResult}
        """
        results = {}
        for ch in chapter_nums:
            results[ch] = self.repair(ch)
        return results

    def dry_run(self, chapter_num: int, issues: List[Issue] = None) -> str:
        """
        预览修复效果（不写入）

        Args:
            chapter_num: 章节编号
            issues: 可选的问题列表

        Returns:
            修复后的内容
        """
        content = self.paths.read_chapter(chapter_num)
        if not content:
            return ""

        new_content, _ = self._apply_rules(content, issues or [])
        return new_content

    @abstractmethod
    def _apply_rules(self, content: str, issues: List[Issue]) -> Tuple[str, int]:
        """
        应用规则替换

        Returns:
            (new_content, change_count)
        """
        raise NotImplementedError("子类必须实现 _apply_rules 方法")

    @abstractmethod
    def _get_rules(self) -> List[Tuple[str, str, str]]:
        """
        获取规则列表

        Returns:
            [(原词, 替换词, 描述), ...]
        """
        raise NotImplementedError("子类必须实现 _get_rules 方法")


class RuleBasedRepairer(Repairer):
    """
    基于规则的修复器基类
    """

    def __init__(self, rules: List[Tuple[str, str, str]] = None, paths: Optional[ProjectPaths] = None):
        super().__init__(paths)
        self._custom_rules = rules

    def _get_rules(self) -> List[Tuple[str, str, str]]:
        if self._custom_rules is not None:
            return self._custom_rules
        return []

    def _apply_rules(self, content: str, issues: List[Issue]) -> Tuple[str, int]:
        rules = self._get_rules()
        count = 0
        result = content

        for old_term, new_term, desc in rules:
            if old_term in result:
                cnt = result.count(old_term)
                result = result.replace(old_term, new_term)
                count += cnt

        return result, count


class YAMLRuleRepairer(Repairer):
    """
    基于YAML配置的修复器
    """

    def __init__(self, rules_file: str, paths: Optional[ProjectPaths] = None):
        super().__init__(paths)
        self.rules_file = rules_file
        self._rules_cache: Optional[List[Dict[str, str]]] = None

    def _load_rules(self) -> List[Dict[str, str]]:
        """加载YAML规则文件"""
        if self._rules_cache is not None:
            return self._rules_cache

        rules_path = self.paths.rules / self.rules_file
        if not rules_path.exists():
            return []

        with open(rules_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self._rules_cache = data.get("rules", [])
        return self._rules_cache

    def _get_rules(self) -> List[Tuple[str, str, str]]:
        rules = self._load_rules()
        result = []
        for rule in rules:
            rule_type = rule.get("type", "replacement")
            source = rule.get("source", "")
            target = rule.get("target", "")
            desc = rule.get("description", "")

            if rule_type == "deletion":
                target = ""

            if source:
                result.append((source, target, desc))

        return result

    def _apply_rules(self, content: str, issues: List[Issue]) -> Tuple[str, int]:
        rules = self._get_rules()
        count = 0
        result = content

        for old_term, new_term, desc in rules:
            if old_term in result:
                cnt = result.count(old_term)
                result = result.replace(old_term, new_term)
                count += cnt

        return result, count
