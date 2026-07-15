"""事实库模块

管理已确认的事实，如"林夜是铁蛋的弟弟"。
事实库存储经过验证的信息，支持按类别、章节查询和事实验证。
"""
from typing import Any, Dict, List, Optional

from infra.memory_system.state.state_manager import MemoryStateManager


class FactBase:
    """事实库

    管理所有已确认的事实，基于 MemoryStateManager 提供持久化存储。
    事实包含：fact_id, content, source_chapter, category, confidence, verified
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化事实库

        Args:
            config: 配置字典，需包含 storage 字段
        """
        self.state_manager = MemoryStateManager(config)

    def add_fact(
        self,
        fact_id: str,
        content: str,
        source_chapter: int,
        category: str,
        confidence: float,
    ) -> None:
        """添加事实

        如果 fact_id 已存在，则更新现有事实。

        Args:
            fact_id: 事实唯一标识符
            content: 事实内容
            source_chapter: 来源章节
            category: 事实类别（如 character_relationship, plot_event 等）
            confidence: 置信度 (0.0 - 1.0)
        """
        all_data = self.state_manager.load("state_file")

        if "facts" not in all_data:
            all_data["facts"] = {}

        # 如果已存在，获取 verified 状态
        existing_fact = all_data["facts"].get(fact_id, {})
        verified = existing_fact.get("verified", False)

        # 构建事实数据
        fact_data = {
            "fact_id": fact_id,
            "content": content,
            "source_chapter": source_chapter,
            "category": category,
            "confidence": confidence,
            "verified": verified,
        }

        all_data["facts"][fact_id] = fact_data
        self.state_manager.save("state_file", all_data)

    def get_fact(self, fact_id: str) -> Optional[Dict[str, Any]]:
        """获取事实

        Args:
            fact_id: 事实唯一标识符

        Returns:
            事实字典，如果不存在则返回 None
        """
        all_data = self.state_manager.load("state_file")
        facts = all_data.get("facts", {})
        return facts.get(fact_id)

    def get_facts_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按类别获取事实

        Args:
            category: 事实类别

        Returns:
            匹配类别的所有事实列表
        """
        all_data = self.state_manager.load("state_file")
        facts = all_data.get("facts", {})

        return [
            fact for fact in facts.values() if fact.get("category") == category
        ]

    def get_facts_by_chapter(self, chapter: int) -> List[Dict[str, Any]]:
        """按章节获取事实

        Args:
            chapter: 章节号

        Returns:
            匹配章节的所有事实列表
        """
        all_data = self.state_manager.load("state_file")
        facts = all_data.get("facts", {})

        return [
            fact for fact in facts.values() if fact.get("source_chapter") == chapter
        ]

    def verify_fact(self, fact_id: str) -> bool:
        """验证事实

        Args:
            fact_id: 事实唯一标识符

        Returns:
            如果事实存在且成功验证返回 True，否则返回 False
        """
        all_data = self.state_manager.load("state_file")
        facts = all_data.get("facts", {})

        if fact_id not in facts:
            return False

        facts[fact_id]["verified"] = True
        self.state_manager.save("state_file", all_data)
        return True

    def get_all_facts(self) -> Dict[str, Dict[str, Any]]:
        """获取所有事实

        Returns:
            所有事实字典，键为 fact_id
        """
        all_data = self.state_manager.load("state_file")
        return all_data.get("facts", {})
