#!/usr/bin/env python3
"""
基础检查器类

所有检查器应继承此基类
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import logging

from ..engine.data_structures import Issue, CheckerType

logger = logging.getLogger(__name__)


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

    def _should_skip_via_whitelist(self, context: Optional[Dict[str, Any]]) -> tuple[bool, str]:
        """
        检查是否应通过白名单跳过检测

        Returns:
            (should_skip, reason)
        """
        if not context:
            return False, ""

        try:
            from ..engine.whitelist_manager import WhitelistManager
            whitelist = WhitelistManager()

            # 构建检查器名称
            checker_name = self.__class__.__name__.replace("Checker", "").lower() + "_checker"

            # 检查是否应跳过
            should_skip, reason = whitelist.should_skip(checker_name, context)

            # 检查是否被反向白名单强制检测
            if should_skip:
                chapter_num = context.get("chapter_num", 0)
                if chapter_num and whitelist.should_force_check(chapter_num, checker_name):
                    logger.info(f"反向白名单覆盖: {checker_name} 在章节 {chapter_num} 强制检测")
                    return False, ""

            return should_skip, reason
        except Exception as e:
            logger.warning(f"白名单检查失败: {e}")
            return False, ""

    def check_with_whitelist(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        带白名单检查的检测方法

        默认实现先检查白名单，如果命中则跳过检测
        子类可以重写此方法以自定义行为
        """
        # 确保context中有chapter_num
        if context is None:
            context = {}
        if "chapter_num" not in context:
            context["chapter_num"] = chapter_num

        # 白名单检查
        should_skip, reason = self._should_skip_via_whitelist(context)
        if should_skip:
            logger.info(f"跳过检测 {self.__class__.__name__} (白名单): {reason}")
            return []

        # 执行实际检测
        return self.check(chapter_content, chapter_num, context)

    def check_realtime(self, text: str, **kwargs) -> List[Issue]:
        """
        实时检查（轻量级）

        默认实现调用check，可被子类重写以提供更快的实时检查
        """
        return []

    def get_checker_type(self) -> CheckerType:
        """获取检查器类型"""
        return self.checker_type