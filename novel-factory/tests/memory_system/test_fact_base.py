"""FactBase 测试"""
import pytest
from pathlib import Path

from infra.memory_system.state.fact_base import FactBase


class TestFactBase:
    """FactBase 测试套件"""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """创建临时状态目录"""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        return state_dir

    @pytest.fixture
    def mock_config(self, temp_state_dir):
        """模拟配置"""
        return {
            "storage": {
                "state_file": str(temp_state_dir / "state_tracker.json"),
                "plot_threads_file": str(temp_state_dir / "plot_threads.yaml"),
                "timeline_file": str(temp_state_dir / "timeline.json"),
            }
        }

    @pytest.fixture
    def fact_base(self, mock_config):
        """创建 FactBase 实例"""
        return FactBase(mock_config)

    def test_add_fact(self, fact_base):
        """测试添加事实"""
        fact_base.add_fact(
            fact_id="fact_001",
            content="林夜是铁蛋的弟弟",
            source_chapter=5,
            category="character_relationship",
            confidence=0.95,
        )

        result = fact_base.get_fact("fact_001")
        assert result is not None
        assert result["fact_id"] == "fact_001"
        assert result["content"] == "林夜是铁蛋的弟弟"
        assert result["source_chapter"] == 5
        assert result["category"] == "character_relationship"
        assert result["confidence"] == 0.95
        assert result["verified"] is False

    def test_add_multiple_facts(self, fact_base):
        """测试添加多个事实"""
        fact_base.add_fact(
            fact_id="fact_001",
            content="林夜是铁蛋的弟弟",
            source_chapter=5,
            category="character_relationship",
            confidence=0.95,
        )
        fact_base.add_fact(
            fact_id="fact_002",
            content="铁蛋首次出现在第一章",
            source_chapter=1,
            category="character_appearance",
            confidence=1.0,
        )

        all_facts = fact_base.get_all_facts()
        assert len(all_facts) == 2
        assert "fact_001" in all_facts
        assert "fact_002" in all_facts

    def test_get_fact_nonexistent(self, fact_base):
        """测试获取不存在的事实"""
        result = fact_base.get_fact("nonexistent_fact")
        assert result is None

    def test_get_facts_by_category(self, fact_base):
        """测试按类别获取事实"""
        fact_base.add_fact(
            fact_id="fact_001",
            content="林夜是铁蛋的弟弟",
            source_chapter=5,
            category="character_relationship",
            confidence=0.95,
        )
        fact_base.add_fact(
            fact_id="fact_002",
            content="铁蛋首次出现在第一章",
            source_chapter=1,
            category="character_appearance",
            confidence=1.0,
        )
        fact_base.add_fact(
            fact_id="fact_003",
            content="林夜住在村庄东边",
            source_chapter=8,
            category="character_relationship",
            confidence=0.8,
        )

        relationship_facts = fact_base.get_facts_by_category("character_relationship")
        assert len(relationship_facts) == 2
        assert all(f["category"] == "character_relationship" for f in relationship_facts)

    def test_get_facts_by_category_nonexistent(self, fact_base):
        """测试按不存在的类别获取事实"""
        result = fact_base.get_facts_by_category("nonexistent_category")
        assert result == []

    def test_get_facts_by_chapter(self, fact_base):
        """测试按章节获取事实"""
        fact_base.add_fact(
            fact_id="fact_001",
            content="林夜是铁蛋的弟弟",
            source_chapter=5,
            category="character_relationship",
            confidence=0.95,
        )
        fact_base.add_fact(
            fact_id="fact_002",
            content="铁蛋首次出现在第一章",
            source_chapter=1,
            category="character_appearance",
            confidence=1.0,
        )
        fact_base.add_fact(
            fact_id="fact_003",
            content="林夜和铁蛋在第五章一起探险",
            source_chapter=5,
            category="plot_event",
            confidence=0.9,
        )

        chapter_5_facts = fact_base.get_facts_by_chapter(5)
        assert len(chapter_5_facts) == 2
        assert all(f["source_chapter"] == 5 for f in chapter_5_facts)

    def test_get_facts_by_chapter_nonexistent(self, fact_base):
        """测试按不存在的章节获取事实"""
        result = fact_base.get_facts_by_chapter(999)
        assert result == []

    def test_verify_fact(self, fact_base):
        """测试验证事实"""
        fact_base.add_fact(
            fact_id="fact_001",
            content="林夜是铁蛋的弟弟",
            source_chapter=5,
            category="character_relationship",
            confidence=0.95,
        )

        # 验证前
        fact = fact_base.get_fact("fact_001")
        assert fact["verified"] is False

        # 验证
        result = fact_base.verify_fact("fact_001")
        assert result is True

        # 验证后
        fact = fact_base.get_fact("fact_001")
        assert fact["verified"] is True

    def test_verify_fact_nonexistent(self, fact_base):
        """测试验证不存在的事实"""
        result = fact_base.verify_fact("nonexistent_fact")
        assert result is False

    def test_get_all_facts_empty(self, fact_base):
        """测试在没有事实时返回空字典"""
        result = fact_base.get_all_facts()
        assert result == {}

    def test_fact_persistence_after_save_load(self, mock_config, temp_state_dir):
        """测试事实数据在保存和加载后保持一致"""
        fact_base1 = FactBase(mock_config)
        fact_base1.add_fact(
            fact_id="fact_001",
            content="林夜是铁蛋的弟弟",
            source_chapter=5,
            category="character_relationship",
            confidence=0.95,
        )
        fact_base1.verify_fact("fact_001")

        # 创建新实例模拟重启
        fact_base2 = FactBase(mock_config)
        result = fact_base2.get_fact("fact_001")

        assert result is not None
        assert result["content"] == "林夜是铁蛋的弟弟"
        assert result["source_chapter"] == 5
        assert result["category"] == "character_relationship"
        assert result["confidence"] == 0.95
        assert result["verified"] is True

    def test_update_fact_confidence(self, fact_base):
        """测试更新事实的置信度"""
        fact_base.add_fact(
            fact_id="fact_001",
            content="林夜是铁蛋的弟弟",
            source_chapter=5,
            category="character_relationship",
            confidence=0.5,
        )

        # 通过重新添加更新置信度
        fact_base.add_fact(
            fact_id="fact_001",
            content="林夜是铁蛋的弟弟",
            source_chapter=5,
            category="character_relationship",
            confidence=0.95,
        )

        result = fact_base.get_fact("fact_001")
        assert result["confidence"] == 0.95

    def test_category_filter_with_no_matches(self, fact_base):
        """测试类别过滤但没有匹配项"""
        fact_base.add_fact(
            fact_id="fact_001",
            content="林夜是铁蛋的弟弟",
            source_chapter=5,
            category="character_relationship",
            confidence=0.95,
        )

        result = fact_base.get_facts_by_category("plot_event")
        assert result == []

    def test_chapter_filter_with_no_matches(self, fact_base):
        """测试章节过滤但没有匹配项"""
        fact_base.add_fact(
            fact_id="fact_001",
            content="林夜是铁蛋的弟弟",
            source_chapter=5,
            category="character_relationship",
            confidence=0.95,
        )

        result = fact_base.get_facts_by_chapter(10)
        assert result == []