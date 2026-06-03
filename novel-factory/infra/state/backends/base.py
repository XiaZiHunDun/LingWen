"""
状态后端抽象接口

提供可切换的状态存储后端（SQLite/JSON）
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class StateBackend(ABC):
    """
    状态后端抽象接口

    用于解耦 hooks/actions 与具体存储实现
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        获取指定键的值

        Args:
            key: 键名

        Returns:
            值，如果不存在返回 None
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        设置指定键的值

        Args:
            key: 键名
            value: 值
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        删除指定键

        Args:
            key: 键名

        Returns:
            是否成功删除
        """
        pass

    @abstractmethod
    def list_keys(self, prefix: Optional[str] = None) -> list[str]:
        """
        列出所有键

        Args:
            prefix: 可选的键前缀过滤

        Returns:
            键列表
        """
        pass
