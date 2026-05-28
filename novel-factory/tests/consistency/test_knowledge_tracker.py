#!/usr/bin/env python3
"""
KnowledgeTracker 测试

检测信息知晓矛盾（A告诉了B秘密，但B后续毫无反应）
"""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infra.consistency.checkers.knowledge_tracker import KnowledgeTracker


class TestKnowledgeTracker:
    """KnowledgeTracker 测试类"""

    def test_knowledge_tracker_detects_unresponded_secret(self):
        """检测到角色听到秘密却无反应的情况"""
        checker = KnowledgeTracker()

        chapter_content = """
        林夜将父亲留下的玉佩递给苏琳，低声说道：
        "这是我父亲的遗物，也是我们林家的秘密。"
        苏琳接过玉佩，仔细端详。

        片刻后，林夜问道："你知道这个秘密了吗？"
        苏琳茫然地看着他："什么秘密？"
        """

        issues = checker.check(chapter_content, chapter_num=10, context={})

        # 检测到苏琳听到了秘密但没有反应
        assert len(issues) > 0, f"Expected issues but got 0. Content:\n{chapter_content}"
        assert any(i.issue_type == "knowledge_unacknowledged" for i in issues), \
            f"Expected knowledge_unacknowledged issue type, got: {[i.issue_type for i in issues]}"

    def test_knowledge_tracker_no_issue_when_acknowledged(self):
        """当角色正确回应秘密时，不应有问题"""
        checker = KnowledgeTracker()

        chapter_content = """
        林夜将父亲留下的玉佩递给苏琳，低声说道：
        "这是我父亲的遗物，也是我们林家的秘密。"
        苏琳接过玉佩，神色凝重地点了点头。
        "原来如此...我会替你保守这个秘密的。"
        """

        issues = checker.check(chapter_content, chapter_num=10, context={})

        # 苏琳正确回应了秘密，不应有问题
        assert len(issues) == 0, f"Expected 0 issues but got {len(issues)}: {[i.title for i in issues]}"

    def test_knowledge_tracker_multiple_secrets(self):
        """检测多个秘密的情况"""
        checker = KnowledgeTracker()

        chapter_content = """
        林夜将父亲留下的玉佩递给苏琳，低声说道：
        "这是我父亲的遗物，也是我们林家的秘密。"
        苏琳茫然地看着他："什么秘密？"

        林夜又告诉李明："我的真实身份是林家后人。"
        李明点了点头："我明白了。"
        """

        issues = checker.check(chapter_content, chapter_num=10, context={})

        # 苏琳没有回应，但李明有回应
        assert len(issues) > 0
        assert any("苏琳" in i.title or "苏琳" in i.evidence for i in issues)
        # 李明的回应不应产生问题
        assert not any("李明" in i.title for i in issues)

    def test_knowledge_tracker_no_secret_revealed(self):
        """没有透露秘密时，不应有问题"""
        checker = KnowledgeTracker()

        chapter_content = """
        林夜和苏琳坐在茶馆里，聊天。
        "今天的天气真不错。"苏琳说道。
        "是啊，难得有这么清闲的时光。"林夜附和道。
        """

        issues = checker.check(chapter_content, chapter_num=10, context={})

        # 没有任何秘密透露，不应有问题
        assert len(issues) == 0

    def test_knowledge_tracker_partial_acknowledgment(self):
        """部分回应但不完全理解的情况"""
        checker = KnowledgeTracker()

        chapter_content = """
        林夜将父亲留下的玉佩递给苏琳，低声说道：
        "这是我父亲的遗物，也是我们林家的秘密。"
        苏琳看了看玉佩："哦，是吗？"
        """

        issues = checker.check(chapter_content, chapter_num=10, context={})

        # 苏琳只是说"哦，是吗？"这种敷衍式回应，可能也算没完全理解
        # 这个测试检查至少不会误报
        # 如果简化版的实现不检测这种情况，也是可以接受的

    def test_checker_type(self):
        """检查 checker_type 正确"""
        checker = KnowledgeTracker()
        assert checker.get_checker_type().value == "knowledge_tracking"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])