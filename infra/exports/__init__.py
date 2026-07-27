#!/usr/bin/env python3
"""
分组导出模块

提供按功能分组的导出方式，减少启动时的导入负担。

使用方式：
    # 按需导入（推荐）
    from infra.exports.core import Result, Ok, Err
    from infra.exports.events import Event, EventStore, create_event
    from infra.exports.persistence import get_connection, register_query
    
    # 批量导入
    from infra.exports import core, events, persistence
"""

from .core import *
from .events import *
from .persistence import *

__all__ = [
    # 模块引用
    "core", "events", "persistence",
]
