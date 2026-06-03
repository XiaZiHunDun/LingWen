#!/usr/bin/env python3
"""
一致性引擎与记忆系统集成测试

测试以下功能：
1. 从记忆系统获取角色状态历史
2. 通过向量检索查找相似情节
3. 检查上下文在运行检查器之前被记忆数据丰富
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infra.consistency.engine.consistency_engine import ConsistencyEngine
from infra.consistency.engine.data_structures import CheckScope, ConsistencyReport


class MockMemoryGateway:
    """模拟记忆网关"""

    def __init__(self, character_states: Dict[str, Dict[str, Any]] = None,
                 pending_foreshadows: Dict[str, Dict[str, Any]] = None,
                 similar_segments: List[Dict[str, Any]] = None):
        """
        初始化模拟记忆网关

        Args:
            character_states: 角色状态字典
            pending_foreshadows: 待回收伏笔
            similar_segments: 相似情节段落
        """
        self._character_states = character_states or {}
        self._pending_foreshadows = pending_foreshadows or {}
        self._similar_segments = similar_segments or []
        self._auto_push_context = {
            "chapter": 1,
            "character_states": self._character_states,
            "pending_foreshadows": self._pending_foreshadows,
            "recent_events": [],
            "related_segments": self._similar_segments
        }

    def get_all_characters(self) -> Dict[str, Dict[str, Any]]:
        """获取所有角色状态"""
        return self._character_states

    def get_character_state(self, character: str) -> Optional[Dict[str, Any]]:
        """获取指定角色状态"""
        return self._character_states.get(character)

    def get_pending_foreshadows(self) -> Dict[str, Dict[str, Any]]:
        """获取待回收伏笔"""
        return self._pending_foreshadows

    def auto_push_context(self, chapter_num: int) -> Dict[str, Any]:
        """自动推送上下文"""
        ctx = self._auto_push_context.copy()
        ctx["chapter"] = chapter_num
        return ctx

    def query(self, query: str, scope: str = "all",
              top_k: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """查询相似段落"""
        return self._similar_segments[:top_k]


class TestMemoryIntegrationInit:
    """测试记忆系统集成初始化"""

    def test_init_with_memory_gateway(self):
        """测试使用记忆网关初始化"""
        mock_gateway = MockMemoryGateway()
        engine = ConsistencyEngine(memory_gateway=mock_gateway)

        assert engine is not None
        assert engine.memory_gateway is mock_gateway

    def test_init_without_memory_gateway(self):
        """测试不使用记忆网关初始化"""
        engine = ConsistencyEngine()

        assert engine is not None
        assert engine.memory_gateway is None


class TestCharacterStateHistory:
    """测试角色状态历史查询"""

    def test_get_character_state_from_memory(self):
        """测试从记忆系统获取角色状态"""
        character_states = {
            "林夜": {
                "current_location": "王宫",
                "current_form": "人形",
                "alive": True,
                "emotion_state": "平静"
            },
            "李明": {
                "current_location": "废墟",
                "current_form": "受伤状态",
                "alive": True,
                "emotion_state": "焦虑"
            }
        }

        mock_gateway = MockMemoryGateway(character_states=character_states)
        engine = ConsistencyEngine(memory_gateway=mock_gateway)

        state = engine.get_character_state_from_memory("林夜")

        assert state is not None
        assert state["current_location"] == "王宫"
        assert state["emotion_state"] == "平静"

    def test_get_nonexistent_character_state(self):
        """测试获取不存在的角色状态"""
        mock_gateway = MockMemoryGateway()
        engine = ConsistencyEngine(memory_gateway=mock_gateway)

        state = engine.get_character_state_from_memory("不存在的角色")

        assert state is None

    def test_character_state_in_context_enrichment(self):
        """测试角色状态在上下文丰富时被包含"""
        character_states = {
            "林夜": {
                "current_location": "王宫",
                "alive": True
            }
        }

        mock_gateway = MockMemoryGateway(character_states=character_states)
        engine = ConsistencyEngine(memory_gateway=mock_gateway)

        content = "林夜站在宫殿门口。"
        context = {}

        enriched = engine._enrich_context_from_memory(
            chapter_num=25,
            chapter_content=content,
            context=context
        )

        assert "character_states" in enriched
        assert "林夜" in enriched["character_states"]
        assert enriched["character_states"]["林夜"]["current_location"] == "王宫"


class TestSimilarPlotRetrieval:
    """测试相似情节检索"""

    def test_query_similar_plots(self):
        """测试查询相似情节"""
        similar_segments = [
            {"text": "林夜与敌人在山崖激战", "chapter": 10, "score": 0.95},
            {"text": "林夜使用新能力击败对手", "chapter": 15, "score": 0.88},
            {"text": "山崖上的最终对决", "chapter": 20, "score": 0.82}
        ]

        mock_gateway = MockMemoryGateway(similar_segments=similar_segments)
        engine = ConsistencyEngine(memory_gateway=mock_gateway)

        results = engine.query_similar_plots("林夜在山崖上战斗", top_k=2)

        assert len(results) == 2
        assert results[0]["text"] == "林夜与敌人在山崖激战"

    def test_similar_plots_in_context_enrichment(self):
        """测试相似情节在上下文丰富时被包含"""
        similar_segments = [
            {"text": "林夜在山崖上战斗", "chapter": 10, "score": 0.9}
        ]

        mock_gateway = MockMemoryGateway(similar_segments=similar_segments)
        engine = ConsistencyEngine(memory_gateway=mock_gateway)

        content = "林夜决定在山崖边迎接挑战。"
        context = {}

        enriched = engine._enrich_context_from_memory(
            chapter_num=25,
            chapter_content=content,
            context=context
        )

        assert "similar_segments" in enriched
        assert len(enriched["similar_segments"]) > 0

    def test_query_without_memory_gateway(self):
        """测试无记忆网关时查询相似情节"""
        engine = ConsistencyEngine()

        results = engine.query_similar_plots("测试查询")

        assert results == []

    def test_extract_plot_query(self):
        """测试从内容中提取查询字符串"""
        engine = ConsistencyEngine()

        content = "林夜站在巍峨的山崖上，俯瞰着脚下的云海，心中充满了决心。"

        query = engine._extract_plot_query(content)

        assert query is not None
        assert len(query) > 0
        assert len(query) <= 200


class TestContextEnrichment:
    """测试上下文丰富功能"""

    def test_context_enriched_without_memory_gateway(self):
        """测试无记忆网关时上下文保持不变"""
        engine = ConsistencyEngine()

        content = "林夜站在山崖上。"
        context = {"existing_key": "value"}

        enriched = engine._enrich_context_from_memory(
            chapter_num=25,
            chapter_content=content,
            context=context
        )

        assert enriched == context

    def test_context_enriched_with_memory_gateway(self):
        """测试有记忆网关时上下文被丰富"""
        character_states = {"林夜": {"current_location": "王宫"}}
        pending_foreshadows = {"fp_001": {"title": "神秘剑客", "status": "pending"}}

        mock_gateway = MockMemoryGateway(
            character_states=character_states,
            pending_foreshadows=pending_foreshadows
        )
        engine = ConsistencyEngine(memory_gateway=mock_gateway)

        content = "林夜开始新冒险。"
        context = {}

        enriched = engine._enrich_context_from_memory(
            chapter_num=25,
            chapter_content=content,
            context=context
        )

        assert "character_states" in enriched
        assert "pending_foreshadows" in enriched
        assert "林夜" in enriched["character_states"]

    def test_check_chapter_enriches_context(self):
        """测试 check_chapter 自动丰富上下文"""
        character_states = {
            "林夜": {"current_location": "王宫", "alive": True}
        }

        mock_gateway = MockMemoryGateway(character_states=character_states)
        engine = ConsistencyEngine(memory_gateway=mock_gateway)

        content = "林夜站在宫殿门口，眺望着远方。"

        report = engine.check_chapter(
            chapter_num=25,
            chapter_content=content
        )

        assert report is not None
        assert isinstance(report, ConsistencyReport)
        # 验证元数据中记录了 memory_enriched
        assert report.metadata.get("memory_enriched") is True


class TestMemoryIntegrationWithCheckers:
    """测试记忆系统与检查器集成"""

    def test_character_checker_receives_character_states(self):
        """测试角色检查器接收到角色状态"""
        character_states = {
            "林夜": {
                "current_location": "王宫",
                "personality_tags": ["冷静"]
            }
        }

        mock_gateway = MockMemoryGateway(character_states=character_states)
        engine = ConsistencyEngine(memory_gateway=mock_gateway)

        content = "林夜在宫殿中冷静地思考着下一步行动。"

        # 直接测试上下文丰富
        enriched = engine._enrich_context_from_memory(
            chapter_num=25,
            chapter_content=content,
            context={}
        )

        assert "character_states" in enriched
        assert enriched["character_states"]["林夜"]["current_location"] == "王宫"

    def test_foreshadow_checker_receives_pending_foreshadows(self):
        """测试伏笔检查器接收到待回收伏笔"""
        pending_foreshadows = {
            "fp_001": {
                "title": "神秘剑客",
                "planted_chapter": 3,
                "status": "pending"
            }
        }

        mock_gateway = MockMemoryGateway(pending_foreshadows=pending_foreshadows)
        engine = ConsistencyEngine(memory_gateway=mock_gateway)

        content = "远处传来一阵神秘的声音。"

        enriched = engine._enrich_context_from_memory(
            chapter_num=25,
            chapter_content=content,
            context={}
        )

        assert "pending_foreshadows" in enriched
        assert "fp_001" in enriched["pending_foreshadows"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
