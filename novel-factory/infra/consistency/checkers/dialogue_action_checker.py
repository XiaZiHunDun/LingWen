#!/usr/bin/env python3
"""
言行不一检测器

检测角色做出承诺后立即采取相反行动的矛盾
如：说"我不会丢下你"然后立刻离开

检测维度（S2逻辑自洽）：
- P1: 承诺后立即违背（说A做B）
"""

import re
from typing import List, Dict, Any, Optional

from infra.consistency.engine.data_structures import (
    Issue, IssueLocation, CheckerType, IssueSeverity
)
from .base_checker import BaseChecker


class DialogueActionChecker(BaseChecker):
    """言行不一检测器 - 检测说A做B的矛盾"""

    # 承诺类对话模式
    PROMISE_PATTERNS = [
        r"\"我不会(.+?)\"",
        r"\"我一定(.+?)\"",
        r"\"我发誓(.+?)\"",
        r"\"我承诺(.+?)\"",
        r"\"(.+?)绝不失言\"",
        r"\"(.+?)一定做到\"",
        r"\"我必然会(.+?)\"",
        r"\"我必定(.+?)\"",
    ]

    # 与承诺相悖的动作模式
    CONTRADICTION_PATTERNS = [
        r"转身离去",
        r"头也不回",
        r"径直离开",
        r"已经走了",
        r"离开(.+?)独自",
        r"留下(.+?)一人",
        r"消失(.+?)身影",
        r"便滑落尘埃",
        r"宝物便滑落",
        r"头也不回地",
        r"毫不留恋",
        r"已不见踪影",
        r"已经离开",
        r"迅速离去",
        r"悄然离去",
    ]

    def __init__(self):
        super().__init__(CheckerType.DIALOGUE_ACTION)

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        issues = []

        # 1. 查找承诺类对话
        promises = self._find_promises(chapter_content)

        for promise_info in promises:
            promise_text = promise_info["text"]
            after_text = promise_info["after_text"]

            # 2. 检查承诺后是否立即出现矛盾动作
            if self._has_contradiction(after_text):
                issues.append(self._create_issue(
                    promise_text, after_text[:100], chapter_num
                ))

        return issues

    def _find_promises(self, text: str) -> List[Dict]:
        """查找承诺类对话"""
        results = []
        for pattern in self.PROMISE_PATTERNS:
            for m in re.finditer(pattern, text):
                end_pos = m.end()
                results.append({
                    "text": m.group(),
                    "after_text": text[end_pos:end_pos+150] if end_pos < len(text) else "",
                    "start_pos": m.start()
                })
        return results

    def _has_contradiction(self, text: str) -> bool:
        """检测是否存在相悖动作"""
        for pattern in self.CONTRADICTION_PATTERNS:
            if re.search(pattern, text):
                return True
        return False

    def _create_issue(self, promise: str, action: str, chapter_num: int) -> Issue:
        return Issue(
            id=f"DA_{chapter_num:03d}",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.DIALOGUE_ACTION,
            issue_type="dialogue_action_contradiction",
            title="言行不一: 承诺与行动相悖",
            description=f"角色做出承诺但随后立即采取相反行动",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"承诺: {promise[:50]}... 行动: {action[:50]}...",
            suggestion="承诺后的行动应与承诺一致，或有过渡说明"
        )


if __name__ == '__main__':
    import sys

    checker = DialogueActionChecker()

    if len(sys.argv) > 1:
        chapter_num = int(sys.argv[1])
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent
        ch_file = project_root / '03_内容仓库' / '04_正文' / f'ch{chapter_num:03d}.md'
        if ch_file.exists():
            content = ch_file.read_text(encoding='utf-8')
            issues = checker.check(content, chapter_num)
            if issues:
                print(f"发现 {len(issues)} 处言行不一问题:")
                for issue in issues:
                    print(f"  {issue.description}")
                    print(f"  证据: {issue.evidence}")
            else:
                print("✅ 言行一致性检查通过")
        else:
            print(f"章节文件不存在: {ch_file}")
    else:
        print("用法: python dialogue_action_checker.py <章节号>")