#!/usr/bin/env python3
"""
一致性引擎测试
"""

import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infra.consistency.engine.consistency_engine import ConsistencyEngine
from infra.consistency.engine.data_structures import CheckScope, IssueSeverity


class TestConsistencyEngineInit:
    """测试一致性引擎初始化"""

    def test_default_init(self):
        engine = ConsistencyEngine()
        assert engine is not None
        # 14 checkers: 9 original + 5 new (scene_pattern, foreshadow_quality, character_agency, timeline_age, battle_visualization)
        # + 4 more (repair_trace, gender_consistency, causal_chain, spatial_transition) = 18 total
        assert len(engine.checkers) == 18

    def test_scope_init(self):
        engine = ConsistencyEngine(scope=CheckScope.CRITICAL)
        assert engine.scope == CheckScope.CRITICAL


class TestConsistencyEngineCheck:
    """测试一致性引擎检查功能"""

    def test_check_chapter_returns_report(self):
        engine = ConsistencyEngine()
        content = "林夜站在山崖上，望着远方的云海。"

        report = engine.check_chapter(
            chapter_num=25,
            chapter_content=content
        )

        assert report is not None
        assert report.chapter == 25
        assert report.check_scope == CheckScope.ALL

    def test_check_chapter_with_issues(self):
        engine = ConsistencyEngine()
        # 包含明显的AI痕迹内容 - 使用格式化表达(立即触发)
        content = """
        林夜走进房间。第一点，他检查了窗户。第二点，他查看了地板。
        第三点，他发现了地上的血迹。

        总之，从这个场景可以看出，这个房间发生过什么。
        """

        report = engine.check_chapter(
            chapter_num=25,
            chapter_content=content
        )

        assert report is not None
        # AI痕迹检查应该能发现问题
        ai_issues = [i for i in report.issues
                     if i.checker_type.value == "ai_gloss_checker"]
        assert len(ai_issues) > 0

    def test_check_chapter_with_context(self):
        engine = ConsistencyEngine()
        content = "林夜使用了瞬移能力出现在敌人身后。"

        context = {
            "character_abilities": {
                "林夜": ["不会武"]
            }
        }

        report = engine.check_chapter(
            chapter_num=25,
            chapter_content=content,
            context=context
        )

        assert report is not None

    def test_check_chapter_scope_critical(self):
        engine = ConsistencyEngine(scope=CheckScope.CRITICAL)
        content = "林夜很愤怒地冲向敌人。"

        context = {
            "character_profiles": {
                "林夜": {
                    "core_personality": ["冷静"],
                    "speech_style": "简洁"
                }
            }
        }

        report = engine.check_chapter(
            chapter_num=25,
            chapter_content=content,
            scope=CheckScope.CRITICAL,
            context=context
        )

        assert report is not None
        assert report.check_scope == CheckScope.CRITICAL


class TestConsistencyEngineRealtime:
    """测试实时检查"""

    def test_realtime_check(self):
        engine = ConsistencyEngine()
        content = "总之，我们可以看出这个结论是正确的。"

        issues = engine.realtime_check(content)

        assert isinstance(issues, list)

    def test_realtime_check_with_ai_phrases(self):
        engine = ConsistencyEngine()
        content = "作为一个AI，我认为这个问题很有趣。"

        issues = engine.realtime_check(content)

        assert len(issues) > 0
        assert any(i.severity == IssueSeverity.P2 for i in issues)


class TestConsistencyEngineGetChecker:
    """测试获取检查器"""

    def test_get_existing_checker(self):
        from infra.consistency.engine.data_structures import CheckerType

        engine = ConsistencyEngine()
        checker = engine.get_checker(CheckerType.CHARACTER)

        assert checker is not None

    def test_get_nonexistent_checker(self):
        engine = ConsistencyEngine()
        # 使用一个不存在的检查器类型
        from infra.consistency.engine.data_structures import CheckerType

        checker = engine.get_checker(CheckerType.ITEM)
        assert checker is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])