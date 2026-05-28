#!/usr/bin/env python3
"""
关系状态突变检测器测试
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infra.consistency.checkers.relationship_state_checker import RelationshipStateChecker
from infra.consistency.engine.data_structures import IssueSeverity


class TestRelationshipStateChecker:
    """测试关系状态突变检测"""

    def test_relationship_state_checker_detects_sudden_trust(self):
        """检测到信任突变（不信任 -> 信任）但无过渡"""
        checker = RelationshipStateChecker()

        chapter_content = """
        林夜冷冷地看着王浩，眼中满是警惕。
        "我绝不会信任你这种人。"林夜说道。

        第二天，王浩递给林夜一瓶水，林夜毫不犹豫地接过来喝了。
        两人对视一眼，仿佛多年的老友。
        """

        issues = checker.check(chapter_content, chapter_num=10, context={})

        # 检测到关系突变（不信任 -> 信任）但无过渡
        assert len(issues) > 0
        assert any(i.issue_type == "relationship_state_change" for i in issues)

    def test_relationship_state_checker_no_issue_with_transition(self):
        """有过渡词时关系变化是合理的"""
        checker = RelationshipStateChecker()

        chapter_content = """
        林夜冷冷地看着王浩，眼中满是警惕。
        "我绝不会信任你这种人。"林夜说道。

        经过多次生死考验，一个月后，王浩递给林夜一瓶水。
        林夜接过来喝了，两人对视一笑，终于建立了信任。
        """

        issues = checker.check(chapter_content, chapter_num=10, context={})

        # 有过渡词，关系变化是合理的
        assert len(issues) == 0

    def test_relationship_state_checker_detects_sudden_enmity(self):
        """检测到敌意突变（友好 -> 敌意）但无过渡"""
        checker = RelationshipStateChecker()

        chapter_content = """
        林夜和王浩并肩作战，共同击败了敌人。
        林夜信任王浩，把他当作最信任的战友。

        突然，林夜拔剑指向王浩，眼中满是敌意。
        "我不会放过你！我憎恨你！"
        """

        issues = checker.check(chapter_content, chapter_num=15, context={})

        assert len(issues) > 0
        assert any(i.issue_type == "relationship_state_change" for i in issues)

    def test_relationship_state_checker_emotional_change(self):
        """检测情感突变（喜欢 -> 讨厌）但无过渡"""
        checker = RelationshipStateChecker()

        chapter_content = """
        苏琳看着陈，眼中满是温柔。
        "我喜欢你。"苏琳轻声说道。

        下一秒，苏琳眼神一变，厌恶地看着陈。
        "我讨厌你！"
        """

        issues = checker.check(chapter_content, chapter_num=20, context={})

        assert len(issues) > 0

    def test_relationship_state_checker_with_transition_emotional(self):
        """有过渡词时情感变化是合理的"""
        checker = RelationshipStateChecker()

        chapter_content = """
        苏琳看着陈，眼中满是温柔。
        "我喜欢你。"苏琳轻声说道。

        经过漫长的冷战，许多事情发生了变化。
        渐渐地，苏琳的眼神变得冷淡。
        "我讨厌你。"她说道。
        """

        issues = checker.check(chapter_content, chapter_num=20, context={})

        # 有过渡词（经过、渐渐地），关系变化是合理的
        assert len(issues) == 0

    def test_relationship_state_checker_p1_severity(self):
        """关系状态突变问题应为P1严重度"""
        checker = RelationshipStateChecker()

        chapter_content = """
        林夜和王浩是多年的老友。
        突然，林夜拔剑刺向王浩，眼中满是杀意。
        """

        issues = checker.check(chapter_content, chapter_num=25, context={})

        if len(issues) > 0:
            assert any(i.severity == IssueSeverity.P1 for i in issues)


class TestRelationshipStateWords:
    """测试关系状态词汇定义"""

    def test_negative_trust_words_defined(self):
        """验证负面信任词汇定义"""
        checker = RelationshipStateChecker()

        assert len(checker.NEGATIVE_TRUST_WORDS) > 0
        assert "不信任" in checker.NEGATIVE_TRUST_WORDS
        assert "怀疑" in checker.NEGATIVE_TRUST_WORDS

    def test_positive_trust_words_defined(self):
        """验证正面信任词汇定义"""
        checker = RelationshipStateChecker()

        assert len(checker.POSITIVE_TRUST_WORDS) > 0
        assert "信任" in checker.POSITIVE_TRUST_WORDS
        assert "相信" in checker.POSITIVE_TRUST_WORDS

    def test_transition_words_defined(self):
        """验证过渡词定义"""
        checker = RelationshipStateChecker()

        assert len(checker.TRANSITION_WORDS) > 0
        assert "经过" in checker.TRANSITION_WORDS
        assert "几天后" in checker.TRANSITION_WORDS
        assert "终于" in checker.TRANSITION_WORDS


class TestRelationshipStateEdgeCases:
    """边缘情况测试"""

    def test_no_negative_or_positive_words(self):
        """没有负面或正面词汇时不应报错"""
        checker = RelationshipStateChecker()

        chapter_content = """
        林夜看着王浩，神色平静。
        他转身离开，没有多说一句话。
        """

        issues = checker.check(chapter_content, chapter_num=30, context={})

        # 没有关系词汇，不应报错
        assert len(issues) == 0

    def test_only_negative_words(self):
        """只有负面词汇时不应报错"""
        checker = RelationshipStateChecker()

        chapter_content = """
        林夜冷冷地看着王浩，眼中满是警惕。
        "我讨厌你！"林夜说道，眼中充满敌意。
        """

        issues = checker.check(chapter_content, chapter_num=30, context={})

        # 只有负面词，没有突变，不应报错
        assert len(issues) == 0

    def test_only_positive_words(self):
        """只有正面词汇时不应报错"""
        checker = RelationshipStateChecker()

        chapter_content = """
        林夜微笑着看着王浩。
        "我信任你。"林夜说道。
        """

        issues = checker.check(chapter_content, chapter_num=30, context={})

        # 只有正面词，没有突变，不应报错
        assert len(issues) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])