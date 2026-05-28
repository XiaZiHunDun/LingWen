#!/usr/bin/env python3
"""
一致性修复器基类
为一致性检测器提供修复能力
"""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyRepairResult:
    """一致性修复结果"""
    chapter: int
    success: bool
    changes: int = 0
    new_content: str = ""
    error: str = ""
    repaired_issues: List[str] = field(default_factory=list)


class BaseConsistencyRepairer:
    """
    一致性修复器基类

    使用方式:
        class CharacterRepairer(BaseConsistencyRepairer):
            def _get_fix_rules(self) -> List[Tuple[str, str, str]]:
                return [("原文本", "修复后", "问题描述"), ...]

            def _apply_fixes(self, content: str, issues: List[Any]) -> Tuple[str, int]:
                # 自定义修复逻辑
                pass
    """

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else self._get_project_root()
        self.chapters_dir = self.project_root / "03_内容仓库" / "04_正文"
        self._rules: Optional[List[Tuple[str, str, str]]] = None

    def _get_project_root(self) -> Path:
        """获取项目根目录"""
        from pathlib import Path
        return Path(__file__).parent.parent.parent.parent

    def repair(self, chapter_num: int, issues: List[Any] = None) -> ConsistencyRepairResult:
        """
        修复单个章节

        Args:
            chapter_num: 章节编号
            issues: 可选的问题列表（用于针对性修复）

        Returns:
            ConsistencyRepairResult修复结果
        """
        content = self._read_chapter(chapter_num)
        if not content:
            return ConsistencyRepairResult(
                chapter=chapter_num,
                success=False,
                error="章节不存在"
            )

        try:
            new_content, changes, repaired = self._apply_fixes(content, issues or [])
            if changes > 0:
                self._write_chapter(chapter_num, new_content)

            return ConsistencyRepairResult(
                chapter=chapter_num,
                success=True,
                changes=changes,
                new_content=new_content,
                repaired_issues=repaired
            )
        except Exception as e:
            logger.exception(f"修复章节{chapter_num}失败: {e}")
            return ConsistencyRepairResult(
                chapter=chapter_num,
                success=False,
                error=str(e)
            )

    def repair_batch(self, chapter_nums: List[int], issues_map: Dict[int, List[Any]] = None) -> Dict[int, ConsistencyRepairResult]:
        """
        批量修复章节

        Args:
            chapter_nums: 章节编号列表
            issues_map: 可选的 {chapter_num: issues} 映射

        Returns:
            {chapter_num: ConsistencyRepairResult}
        """
        results = {}
        for ch in chapter_nums:
            issues = issues_map.get(ch) if issues_map else None
            results[ch] = self.repair(ch, issues)
        return results

    def dry_run(self, chapter_num: int, issues: List[Any] = None) -> str:
        """
        预览修复效果（不写入）

        Args:
            chapter_num: 章节编号
            issues: 可选的问题列表

        Returns:
            修复后的内容
        """
        content = self._read_chapter(chapter_num)
        if not content:
            return ""

        new_content, _, _ = self._apply_fixes(content, issues or [])
        return new_content

    def _read_chapter(self, chapter_num: int) -> str:
        """读取章节内容"""
        ch_file = self.chapters_dir / f"ch{chapter_num:03d}.md"
        if not ch_file.exists():
            return ""
        return ch_file.read_text(encoding="utf-8")

    def _write_chapter(self, chapter_num: int, content: str) -> None:
        """写入章节内容"""
        ch_file = self.chapters_dir / f"ch{chapter_num:03d}.md"
        ch_file.write_text(content, encoding="utf-8")

    @abstractmethod
    def _apply_fixes(self, content: str, issues: List[Any]) -> Tuple[str, int, List[str]]:
        """
        应用修复

        Returns:
            (new_content, change_count, repaired_issue_descriptions)
        """
        pass

    def _get_fix_rules(self) -> List[Tuple[str, str, str]]:
        """
        获取修复规则

        Returns:
            [(原文本, 修复后, 问题描述), ...]
        """
        return []

    def _apply_rule_based_fixes(self, content: str) -> Tuple[str, int, List[str]]:
        """应用基于规则的修复"""
        rules = self._get_fix_rules()
        if not rules:
            return content, 0, []

        count = 0
        repaired = []
        result = content

        for old_term, new_term, desc in rules:
            if old_term in result:
                cnt = result.count(old_term)
                result = result.replace(old_term, new_term)
                count += cnt
                repaired.append(f"{desc}: {cnt}处")

        return result, count, repaired


# Import all repairers
from .character_repairer import CharacterRepairer
from .causal_chain_repairer import CausalChainRepairer
from .pacing_repairer import PacingRepairer
from .scene_transition_repairer import SceneTransitionRepairer
from .dialogue_authenticity_repairer import DialogueAuthenticityRepairer
from .gender_consistency_repairer import GenderConsistencyRepairer
from .relationship_state_repairer import RelationshipStateRepairer
from .core_foreshadow_repairer import CoreForeshadowRepairer
from .core_props_repairer import CorePropsRepairer

from pathlib import Path
