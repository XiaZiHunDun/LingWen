#!/usr/bin/env python3
"""
基础检查器类

所有检查器应继承此基类
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..engine.data_structures import Issue, CheckerType


class BaseChecker(ABC):
    """检查器基类"""

    def __init__(self, checker_type: CheckerType):
        self.checker_type = checker_type

    @abstractmethod
    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        执行检查

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 上下文信息（角色档案、物品状态等）

        Returns:
            Issue列表
        """
        pass

    def check_realtime(self, text: str, **kwargs) -> List[Issue]:
        """
        实时检查（轻量级）

        默认实现调用check，可被子类重写以提供更快的实时检查
        """
        return []

    def get_checker_type(self) -> CheckerType:
        """获取检查器类型"""
        return self.checker_type