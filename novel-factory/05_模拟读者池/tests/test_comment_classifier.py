#!/usr/bin/env python3
"""
Reader Feedback Classifier Tests

Tests for the comment_classifier module that maps reader feedback to P0/P1/P2 severity.
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from comment_classifier import classify_reader_feedback, get_severity_label


class TestP0Classification:
    """Tests for P0 severity classification - severe issues that invalidate major plot points"""

    def test_plot_contradiction(self):
        """P0: Plot breaks and contradictions"""
        feedback = "这段情节完全讲不通，前面说主角已经死了，后面又说他在跟别人聊天，这是前后矛盾"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 0, "Plot contradiction should be P0"
        assert issue_type == "logic_inconsistency"

    def test_timeline_contradiction(self):
        """P0: Timeline contradictions"""
        feedback = "第三章说主角穿越前是2020年，第五章又说他是2019年出生的，时间线对不上"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 0, "Timeline contradiction should be P0"
        assert issue_type == "logic_inconsistency"

    def test_character_death_inconsistency(self):
        """P0: Character death inconsistency"""
        feedback = "这个角色明明在第五章已经死了，到第八章又活蹦乱跳地出现，死而复生也太离谱"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 0, "Character death inconsistency should be P0"
        assert issue_type == "logic_inconsistency"

    def test_world_building_contradiction(self):
        """P0: Core world-building contradiction"""
        feedback = "前面设定这个世界没有魔法，突然主角就用出魔法来了，力量体系崩塌"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 0, "World-building contradiction should be P0"
        assert issue_type == "logic_inconsistency"

    def test_major_plot_invalidation(self):
        """P0: Plot point that invalidates the entire story"""
        feedback = "如果主角的妹妹没死，那整个复仇主线就废了，前面都是白写的"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 0, "Major plot invalidation should be P0"
        assert issue_type == "logic_inconsistency"


class TestP1Classification:
    """Tests for P1 severity classification - character behavior or plot gaps"""

    def test_character_behavior_inconsistent(self):
        """P1: Character behavior inconsistent with established personality"""
        feedback = "主角性格突然变了，之前是个聪明人，这里突然降智做傻事，人设崩塌"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 1, "Character behavior inconsistency should be P1"
        assert issue_type == "character_behavior"

    def test_scene_transition_gap(self):
        """P1: Logical gaps in scene transitions"""
        feedback = "上一秒还在皇宫，下一秒就到了战场，场景跳跃太大，过渡不自然"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 1, "Scene transition gap should be P1"
        assert issue_type == "plot_hole"

    def test_foreshadow_not_paid_off(self):
        """P1: Missing foreshadow payoff"""
        feedback = "第一章埋下的伏笔说主角有神秘身世，到大结局都没交代，伏笔没回收"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 1, "Foreshadow not paid off should be P1"
        assert issue_type == "plot_hole"

    def test_unfulfilled_emotional_expectation(self):
        """P1: Unfulfilled emotional expectations"""
        feedback = "本来以为高潮会很感人，结果情绪完全不到位，感动不了人"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 1, "Unfulfilled emotional expectation should be P1"
        assert issue_type == "emotional_disconnect"

    def test_plot_hole_transition(self):
        """P1: Plot hole - sudden unexplained change"""
        feedback = "突然就有了一个亿的资金，前面也没说他是富二代，情节跳跃太快"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 1, "Plot hole should be P1"
        assert issue_type == "plot_hole"


class TestP2Classification:
    """Tests for P2 severity classification - style, pacing, minor issues"""

    def test_style_inconsistency(self):
        """P2: Style inconsistency"""
        feedback = "前面文笔很优美，后面突然变得很口语化，风格突变"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 2, "Style inconsistency should be P2"
        assert issue_type == "style_issue"

    def test_pacing_too_slow(self):
        """P2: Minor pacing issue - too slow"""
        feedback = "节奏有点拖沓，进展太慢，看得有点无聊"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 2, "Pacing issue should be P2"
        assert issue_type == "pacing_issue"

    def test_repetitive_sentence_patterns(self):
        """P2: Repetitive sentence patterns"""
        feedback = "句式重复太多，表达单调，用词重复，词汇贫乏"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 2, "Repetitive patterns should be P2"
        assert issue_type == "style_issue"

    def test_minor_emotional_gap(self):
        """P2: Minor emotional resonance gap"""
        feedback = "情感描写略显平淡，读起来差一点感觉，代入感稍微不够"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 2, "Minor emotional gap should be P2"
        assert issue_type == "emotional_disconnect"

    def test_template_sentence(self):
        """P2: Template sentence pattern repetition"""
        feedback = "这章又是模板句104章，同一个套路用太多次了"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 2, "Template sentences should be P2"
        assert issue_type == "style_issue"


class TestEdgeCases:
    """Edge case tests"""

    def test_empty_feedback(self):
        """Empty feedback should return P2 other"""
        issue_type, severity, reasoning = classify_reader_feedback("")
        assert severity == 2
        assert issue_type == "other"

    def test_whitespace_only(self):
        """Whitespace only feedback should return P2 other"""
        issue_type, severity, reasoning = classify_reader_feedback("   ")
        assert severity == 2
        assert issue_type == "other"

    def test_unmatched_feedback(self):
        """Unmatched feedback should default to P2 other"""
        feedback = "这章写得真好，情节很紧凑，看得我停不下来"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 2
        assert issue_type == "other"

    def test_get_severity_label(self):
        """Test severity label conversion"""
        assert get_severity_label(0) == "P0"
        assert get_severity_label(1) == "P1"
        assert get_severity_label(2) == "P2"
        assert get_severity_label(99) == "P2"  # Default to P2 for unknown


class TestMultipleIssues:
    """Test classification when multiple issues could be present"""

    def test_p0_takes_priority_over_p1(self):
        """When both P0 and P1 patterns match, P0 takes priority"""
        feedback = "前面说主角死了，后面又说他是人设崩塌，逻辑硬伤太严重"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 0, "P0 should take priority"

    def test_p1_takes_priority_over_p2(self):
        """When both P1 and P2 patterns match, P1 takes priority"""
        feedback = "主角性格变了，节奏也有点拖，人设崩塌比较严重"
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        assert severity == 1, "P1 should take priority over P2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])