#!/usr/bin/env python3
"""
检测器基类
所有检测器应继承此类
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.paths import ProjectPaths

# 允许与 consistency 子系统的 IssueSeverity 互操作
try:
    from infra.consistency.engine.data_structures import IssueSeverity
    _SeverityType = Union[str, IssueSeverity]
except ImportError:
    _SeverityType = str  # type: ignore[misc]


@dataclass
class Issue:
    """问题描述

    severity 接受 str（如 "P0"/"P1"/"P2"/"P3"）或 IssueSeverity 枚举值。
    实际存储和比较统一使用 str 值。
    """
    chapter: int
    dimension: str          # 问题维度
    issue_type: str         # 问题类型
    severity: _SeverityType  # P0/P1/P2/P3 (str 或 IssueSeverity)
    description: str        # 问题描述
    location: str = ""      # 位置
    evidence: str = ""       # 证据
    suggestion: str = ""    # 建议修复方案

    def __post_init__(self):
        # 归一化：Enum 转 str，避免后续字符串比较失败
        if hasattr(self.severity, "value"):
            self.severity = self.severity.value


class Inspector:
    """
    检测器基类

    使用方式:
        class WorldviewInspector(Inspector):
            def check(self, chapter_num: int) -> List[Issue]:
                # 实现检测逻辑
                ...
    """

    def __init__(self, paths: Optional[ProjectPaths] = None):
        self.paths = paths or ProjectPaths.get()

    def check(self, chapter_num: int) -> List[Issue]:
        """
        检测单个章节

        Args:
            chapter_num: 章节编号

        Returns:
            发现的问题列表
        """
        raise NotImplementedError("子类必须实现 check 方法")

    def check_batch(self, chapter_nums: List[int]) -> List[Issue]:
        """
        批量检测章节

        Args:
            chapter_nums: 章节编号列表

        Returns:
            所有发现的问题列表
        """
        results = []
        for ch in chapter_nums:
            results.extend(self.check(ch))
        return results

    def read_chapter(self, chapter_num: int) -> str:
        """读取章节内容"""
        return self.paths.read_chapter(chapter_num)

    def get_chapter_context(self, chapter_num: int, before: int = 1, after: int = 1) -> Dict[int, str]:
        """获取章节前后文"""
        context = {}
        for offset in range(-before, after + 1):
            cn = chapter_num + offset
            if 1 <= cn <= 360 and cn != chapter_num:
                content = self.read_chapter(cn)
                if content:
                    context[cn] = content[:500]
        return context


class RuleBasedInspector(Inspector):
    """
    基于规则的检测器基类

    适用于世界观检测、AI痕迹检测等规则明确的场景
    """

    def __init__(self, rules: List[str], paths: Optional[ProjectPaths] = None):
        super().__init__(paths)
        self.rules = rules

    def check(self, chapter_num: int) -> List[Issue]:
        content = self.read_chapter(chapter_num)
        if not content:
            return []

        issues = []
        for rule in self.rules:
            if rule in content:
                count = content.count(rule)
                issues.append(Issue(
                    chapter=chapter_num,
                    dimension=self.dimension,
                    issue_type=self.issue_type,
                    severity="P2",
                    description=f"发现{count}处违规模式: {rule}",
                    location=f"全文约{count}处"
                ))
        return issues


class LLMBasedInspector(Inspector):
    """
    基于LLM的检测器基类

    适用于角色一致性等需要语义理解的任务
    """

    def __init__(self, paths: Optional[ProjectPaths] = None):
        super().__init__(paths)
        self._llm_service = None

    @property
    def llm_service(self):
        """延迟加载LLM服务"""
        if self._llm_service is None:
            from infra.llm_service import LLMService
            self._llm_service = LLMService.get()
        return self._llm_service

    def check(self, chapter_num: int) -> List[Issue]:
        """使用LLM检测章节（子类需实现prompt构建）"""
        raise NotImplementedError("子类必须实现 check 方法")

    def build_prompt(self, chapter_num: int, content: str) -> str:
        """构建检测提示（子类需实现）"""
        raise NotImplementedError("子类必须实现 build_prompt 方法")

    def parse_response(self, response: str) -> List[Issue]:
        """解析LLM响应（子类需实现）"""
        raise NotImplementedError("子类必须实现 parse_response 方法")
