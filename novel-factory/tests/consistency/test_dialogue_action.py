#!/usr/bin/env python3
"""
言行不一检测器测试
检测说A做B的矛盾（如承诺后立即违背）
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infra.consistency.checkers.dialogue_action_checker import DialogueActionChecker
from infra.consistency.engine.data_structures import IssueSeverity


class TestDialogueActionChecker:
    """言行不一检测器测试"""

    def test_dialogue_action_checker_detects_promise_break(self):
        """检测承诺后立即违背的情况"""
        checker = DialogueActionChecker()

        chapter_content = """
        林夜紧紧握住苏琳的手，眼中满是坚定。
        "我不会丢下你，永远不会。"他低声说道。

        话音未落，林夜已经转身离去，只留下苏琳一人站在原地。
        """

        issues = checker.check(chapter_content, chapter_num=10, context={})

        assert len(issues) > 0
        assert any(i.issue_type == "dialogue_action_contradiction" for i in issues)

    def test_dialogue_action_checker_no_issue_when_consistent(self):
        """行为与承诺一致时无问题"""
        checker = DialogueActionChecker()

        chapter_content = """
        林夜紧紧握住苏琳的手，眼中满是坚定。
        "我不会丢下你，永远不会。"他低声说道。

        他转身面对敌人，挡在苏琳身前，誓死守护。
        """

        issues = checker.check(chapter_content, chapter_num=10, context={})

        # 行为与承诺一致
        assert len(issues) == 0

    def test_dialogue_action_checker_promise_with_oath(self):
        """检测发誓类承诺的违背"""
        checker = DialogueActionChecker()

        chapter_content = """
        莫言举起右手，郑重发誓：
        "我发誓，一定会救你出来！"

        话音刚落，莫言已经头也不回地离开了地牢。
        """

        issues = checker.check(chapter_content, chapter_num=20, context={})

        assert len(issues) > 0
        assert any(i.issue_type == "dialogue_action_contradiction" for i in issues)

    def test_dialogue_action_checker_no_issue_pledge_fulfilled(self):
        """承诺被履行时无问题"""
        checker = DialogueActionChecker()

        chapter_content = """
        林夜举起长剑，剑指苍穹。
        "我承诺，必将斩杀暗皇，为所有同胞报仇！"

        他大喝一声，剑光如虹，直取暗皇首级。
        """

        issues = checker.check(chapter_content, chapter_num=30, context={})

        assert len(issues) == 0

    def test_dialogue_action_checker_multiple_promises(self):
        """多个承诺的检测"""
        checker = DialogueActionChecker()

        chapter_content = """
        林夜看着苏琳，轻声说道：
        "我不会离开你的。"
        "我永远会保护你。"

        随后，他转身面对暗皇，挡在了苏琳身前。
        """

        issues = checker.check(chapter_content, chapter_num=40, context={})

        # 两个承诺都一致，行为与承诺相符
        assert len(issues) == 0

    def test_dialogue_action_checker_severity(self):
        """检测到问题时的严重程度"""
        checker = DialogueActionChecker()

        chapter_content = """
        林夜紧紧握住苏琳的手。
        "我一定不会丢下你。"

        话音未落，林夜已经转身离去。
        """

        issues = checker.check(chapter_content, chapter_num=50, context={})

        assert len(issues) > 0
        # 言行不一应该是P1严重问题
        assert any(i.severity == IssueSeverity.P1 for i in issues)

    def test_dialogue_action_checker_promise_commit(self):
        """检测承诺类句式"""
        checker = DialogueActionChecker()

        chapter_content = """
        莫言郑重说道：
        "我承诺，必将此物完好无损地交给你。"

        不料，他刚转身，手中宝物便滑落尘埃。
        """

        issues = checker.check(chapter_content, chapter_num=60, context={})

        assert len(issues) > 0

    def test_dialogue_action_checker_no_false_positive_transition(self):
        """合理的场景转换不是问题"""
        checker = DialogueActionChecker()

        chapter_content = """
        林夜紧紧握住苏琳的手。
        "我不会离开你。"

        画面一转，林夜已经回到了自己的房间。
        他躺在床上，回想着今天的战斗。
        """

        issues = checker.check(chapter_content, chapter_num=70, context={})

        # 场景转换（画面一转）不算违背承诺
        assert len(issues) == 0

    def test_dialogue_action_checker_empty_content(self):
        """空内容无问题"""
        checker = DialogueActionChecker()

        issues = checker.check("", chapter_num=1, context={})

        assert len(issues) == 0

    def test_dialogue_action_checker_no_promise(self):
        """没有承诺时无问题"""
        checker = DialogueActionChecker()

        chapter_content = """
        林夜走进房间，仔细检查了每一个角落。
        他发现地上有一些奇怪的痕迹。
        """

        issues = checker.check(chapter_content, chapter_num=80, context={})

        assert len(issues) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])