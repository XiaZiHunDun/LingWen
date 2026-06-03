"""时间线管理模块

管理事件时间线：
- 记录事件发生的时间点
- 支持按时间范围查询事件
- 支持按章节查询事件
"""
from typing import Any, Dict, List, Optional

from infra.memory_system.state.state_manager import MemoryStateManager


class TimelineManager:
    """时间线管理器

    管理所有事件的时间线信息，基于 MemoryStateManager 提供持久化存储。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化时间线管理器

        Args:
            config: 配置字典，需包含 storage 字段
        """
        self.state_manager = MemoryStateManager(config)

    def add_event(
        self,
        event_id: str,
        timestamp: str,
        description: str,
        chapter: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """添加事件

        Args:
            event_id: 事件唯一标识
            timestamp: 时间戳（ISO 格式）
            description: 事件描述
            chapter: 章节号
            metadata: 额外元数据（可选）

        Returns:
            添加的事件字典
        """
        all_data = self.state_manager.load("timeline_file")

        if "events" not in all_data:
            all_data["events"] = []

        event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "description": description,
            "chapter": chapter,
            "metadata": metadata or {}
        }

        all_data["events"].append(event)
        self.state_manager.save("timeline_file", all_data)

        return event

    def get_all_events(self) -> List[Dict[str, Any]]:
        """获取所有事件

        Returns:
            所有事件列表，按添加顺序排列
        """
        all_data = self.state_manager.load("timeline_file")
        return all_data.get("events", [])

    def get_events_in_range(
        self,
        start_time: str,
        end_time: str
    ) -> List[Dict[str, Any]]:
        """获取时间范围内的事件

        Args:
            start_time: 开始时间（ISO 格式）
            end_time: 结束时间（ISO 格式）

        Returns:
            时间范围内的事件列表
        """
        try:
            start = self._parse_timestamp(start_time)
            end = self._parse_timestamp(end_time)
        except (ValueError, TypeError):
            return []

        all_data = self.state_manager.load("timeline_file")
        events = all_data.get("events", [])

        return [
            event for event in events
            if self._is_timestamp_in_range(event["timestamp"], start, end)
        ]

    def get_events_by_chapter(self, chapter: int) -> List[Dict[str, Any]]:
        """获取指定章节的事件

        Args:
            chapter: 章节号

        Returns:
            指定章节的事件列表
        """
        all_data = self.state_manager.load("timeline_file")
        events = all_data.get("events", [])

        return [event for event in events if event["chapter"] == chapter]

    def _parse_timestamp(self, timestamp: str) -> Optional[str]:
        """解析时间戳为 ISO 格式

        Args:
            timestamp: 时间戳字符串

        Returns:
            ISO 格式时间戳，如果解析失败返回 None
        """
        try:
            # 验证时间戳格式
            from datetime import datetime
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return timestamp
        except (ValueError, AttributeError):
            return None

    def _is_timestamp_in_range(
        self,
        timestamp: str,
        start: str,
        end: str
    ) -> bool:
        """检查时间戳是否在范围内

        Args:
            timestamp: 要检查的时间戳
            start: 开始时间
            end: 结束时间

        Returns:
            是否在范围内
        """
        try:
            from datetime import datetime
            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            s = datetime.fromisoformat(start.replace('Z', '+00:00'))
            e = datetime.fromisoformat(end.replace('Z', '+00:00'))
            return s <= ts <= e
        except (ValueError, AttributeError, TypeError):
            return False