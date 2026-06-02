#!/usr/bin/env python3
"""
基础检查器类

所有检查器应继承此基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
import logging

from ..engine.data_structures import Issue, CheckerType

logger = logging.getLogger(__name__)


class CheckerRegistry:
    """检查器注册表（自动维护）

    BaseChecker 的子类通过声明 `_checker_type` 类属性自动注册到此表。
    ConsistencyEngine 通过 `instantiate_all()` 获取所有已注册的检查器，
    新增/删除检查器无需修改 engine.py。
    """

    _registry: Dict[CheckerType, Type["BaseChecker"]] = {}

    @classmethod
    def register(
        cls,
        checker_type: CheckerType,
        checker_cls: Type["BaseChecker"],
    ) -> None:
        if checker_type in cls._registry:
            existing = cls._registry[checker_type]
            if existing is not checker_cls:
                raise ValueError(
                    f"CheckerType {checker_type} 已被 {existing.__name__} 注册，"
                    f"不能再次注册到 {checker_cls.__name__}"
                )
        cls._registry[checker_type] = checker_cls

    @classmethod
    def get(cls, checker_type: CheckerType) -> Optional[Type["BaseChecker"]]:
        return cls._registry.get(checker_type)

    @classmethod
    def instantiate_all(cls) -> Dict[CheckerType, "BaseChecker"]:
        return {t: c() for t, c in cls._registry.items()}

    @classmethod
    def all_types(cls) -> List[CheckerType]:
        return list(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        """清空注册表（仅用于测试）"""
        cls._registry.clear()


class BaseChecker(ABC):
    """检查器基类

    子类需声明 `_checker_type` 类属性指向对应的 CheckerType 枚举值，
    即可自动注册到 CheckerRegistry。

    Example:
        class CharacterChecker(BaseChecker):
            _checker_type = CheckerType.CHARACTER
            def __init__(self, rules=None):
                super().__init__(self._checker_type)
                self.rules = rules or self._default_rules()
    """

    # 子类设置此属性即可自动注册到 CheckerRegistry
    # 不设置 = 不注册（适用于中间抽象类）
    _checker_type: Optional[CheckerType] = None

    def __init__(self, checker_type: CheckerType):
        self.checker_type = checker_type

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        ctype = getattr(cls, "_checker_type", None)
        if ctype is not None:
            CheckerRegistry.register(ctype, cls)

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
            logger.warning(f"白名单检查失败（默认不跳过）: {e}")
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
