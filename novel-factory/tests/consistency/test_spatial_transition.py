#!/usr/bin/env python3
"""
空间位置突兀转移检测器测试
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infra.consistency.checkers.spatial_transition_checker import SpatialTransitionChecker
from infra.consistency.engine.data_structures import IssueSeverity


class TestSpatialTransitionChecker:
    """测试空间位置突兀转移检测"""

    def test_spatial_transition_detects_instant_movement(self):
        """检测到瞬移类突兀空间转移"""
        checker = SpatialTransitionChecker()

        chapter_content = """
        林夜站在客厅之中，神色凝重。
        突然，一道光芒闪过，林夜直接出现在厨房里。
        """

        issues = checker.check(chapter_content, chapter_num=10, context={})

        assert len(issues) > 0
        assert any(i.issue_type == "spatial_transition" for i in issues)

    def test_spatial_transition_no_issue_with_transition_word(self):
        """使用过渡词时不应报错"""
        checker = SpatialTransitionChecker()

        chapter_content = """
        林夜站在客厅之中，神色凝重。
        他转身离开客厅，穿过走廊，来到厨房。
        """

        issues = checker.check(chapter_content, chapter_num=10, context={})

        assert len(issues) == 0

    def test_spatial_transition_detects_sudden_appear(self):
        """检测'突然出现在'模式"""
        checker = SpatialTransitionChecker()

        chapter_content = """
        苏琳在房间里等待。
        突然出现在门口。
        """

        issues = checker.check(chapter_content, chapter_num=15, context={})

        # 应该有检测到问题
        assert len(issues) > 0

    def test_spatial_transition_with_transition_words_allowed(self):
        """有过渡词时允许空间移动"""
        checker = SpatialTransitionChecker()

        # 使用了"穿过"过渡词
        chapter_content = """
        林夜穿过大门，来到庭院中。
        """

        issues = checker.check(chapter_content, chapter_num=20, context={})

        assert len(issues) == 0

    def test_spatial_transition_multiple_patterns(self):
        """测试多种突兀转移模式"""
        checker = SpatialTransitionChecker()

        chapter_content = """
        莫言站在山崖边。
        下一秒出现在山谷底部。
        """

        issues = checker.check(chapter_content, chapter_num=25, context={})

        assert len(issues) > 0

    def test_spatial_transition_p1_severity(self):
        """空间转移问题应为P1严重度"""
        checker = SpatialTransitionChecker()

        chapter_content = """
        陈站在窗前思考。
        瞬间来到另一个房间。
        """

        issues = checker.check(chapter_content, chapter_num=30, context={})

        if len(issues) > 0:
            assert any(i.severity == IssueSeverity.P1 for i in issues)


class TestSpatialTransitionPatterns:
    """测试空间转移模式匹配"""

    def test_sudden_transition_patterns(self):
        """验证突兀转移模式定义"""
        checker = SpatialTransitionChecker()

        assert len(checker.SUDDEN_TRANSITION_PATTERNS) > 0
        assert any("突然出现在" in p for p in checker.SUDDEN_TRANSITION_PATTERNS)

    def test_transition_words_defined(self):
        """验证过渡词定义"""
        checker = SpatialTransitionChecker()

        assert len(checker.TRANSITION_WORDS) > 0
        assert "穿过" in checker.TRANSITION_WORDS
        assert "来到" in checker.TRANSITION_WORDS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])