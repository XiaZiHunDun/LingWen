"""
状态后端模块

提供可切换的状态存储后端实现
"""

from .base import StateBackend
from .sqlite import SQLiteBackend
from .json import JSONBackend

__all__ = ["StateBackend", "SQLiteBackend", "JSONBackend"]