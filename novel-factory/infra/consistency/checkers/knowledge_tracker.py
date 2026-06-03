#!/usr/bin/env python3
"""
KnowledgeTracker - 信息知晓追踪检测器

检测信息知晓矛盾（A告诉了B秘密，但B后续毫无反应）
"""

import re
from typing import Any, Dict, List, Optional

from ..engine.data_structures import CheckerType, Issue, IssueLocation, IssueSeverity
from .base_checker import BaseChecker


class KnowledgeTracker(BaseChecker):
    """信息知晓追踪检测器 - 检测角色知道某事却无反应"""
    _checker_type = CheckerType.KNOWLEDGE_TRACKING


    # 透露秘密的动作模式
    REVEAL_PATTERNS = [
        r"告诉了?(.+?)秘密",
        r"向(.+?)透露(.+?)秘密",
        r"将(.+?)秘密告诉(.+?)",
        r"告诉(.+?)这是(.+)的(.+)秘密",
        r"告诉(.+?)关于(.+)的秘密",
        r"向(.+?)讲述(.+)的秘密",
        # 新增：描述秘密内容（如"这是我们林家的秘密"）
        r"这是(.+?)的秘密",
        r"我们(.+?)的秘密",
        r"家族的秘密",
        r"父亲的遗物",
        # 透露身份
        r"我的真实身份是(.+?)",
        r"其实我是(.+?)",
        r"我是(.+?)的后人",
    ]

    # 接收秘密的角色模式（在秘密描述之前出现）
    LISTENER_PATTERNS = [
        r"递给(\w+)",
        r"给(\w+)",
        r"向(\w+)",
        r"对(\w+)说",
        r"对(\w+)道",
        r"对(\w+)低声",
        r"对(\w+)低语",
        r"(\w+)接过",
    ]

    # 不知道/茫然的反应模式
    IGNORANCE_PATTERNS = [
        "不知道", "茫然", "疑惑", "困惑", "什么秘密", "什么意思",
        "听不懂", "不明白", "没听懂", "不清楚", "什么", "啥",
        "茫然地看着", "一脸疑惑", "很困惑", "不明白他的意思"
    ]

    # 正确回应的模式
    ACKNOWLEDGMENT_PATTERNS = [
        "点了点头", "神色凝重", "明白了", "知道了", "原来如此",
        "我明白了", "我知道了", "会保守秘密", "替你保密",
        "会守口如瓶", "明白了他的意思", "心中了然",
        "郑重点头", "眼神凝重", "若有所思地点头"
    ]

    def __init__(self):
        super().__init__(self._checker_type)

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        issues = []

        # 1. 查找透露秘密的动作
        secrets_revealed = self._find_secret_reveals(chapter_content)

        for secret_info in secrets_revealed:
            listener = secret_info["listener"]
            secret = secret_info["secret"]

            # 2. 检查listener在之后是否表现出茫然
            after_text = secret_info["after_text"]
            if self._shows_ignorance(after_text):
                # 只有当茫然出现在承认之前时，才算问题
                if not self._has_prior_acknowledgment(after_text):
                    issues.append(self._create_issue(
                        listener, secret, chapter_num, secret_info["match_text"]
                    ))

        return issues

    def _has_prior_acknowledgment(self, text: str) -> bool:
        """检查在茫然之前是否有承认（同一对话块内）"""
        # 找到茫然的位置
        ignorance_pos = len(text)  # 默认在末尾
        for pat in self.IGNORANCE_PATTERNS:
            idx = text.find(pat)
            if idx != -1 and idx < ignorance_pos:
                ignorance_pos = idx

        # 检查在茫然之前是否有承认
        before_ignorance = text[:ignorance_pos]
        for pat in self.ACKNOWLEDGMENT_PATTERNS:
            if pat in before_ignorance:
                return True
        return False

    def _find_secret_reveals(self, text: str) -> List[Dict]:
        """查找透露秘密的动作"""
        results = []

        # 首先尝试找"递给X" + "秘密"的组合
        listener_patterns = [
            (r"递给(\w+)", "递给"),
            (r"给(\w+)看", "给"),
            (r"对(\w+)说", "对"),
            (r"对(\w+)道", "对"),
            (r"对(\w+)低声", "对"),
            (r"对(\w+)低语", "对"),
            (r"(\w+)接过", "接过"),
        ]

        # 查找所有可能的秘密揭示
        secret_patterns = [
            r"这是.+?的秘密",
            r"我们.+?的秘密",
            r"这是父亲的遗物",
            r"也是.+?的秘密",
            r"家族的秘密",
            r"我的真实身份是(.+?)",
            r"其实我是(.+?)",
        ]

        for listener_pattern, listener_keyword in listener_patterns:
            listener_matches = list(re.finditer(listener_pattern, text))
            for listener_match in listener_matches:
                listener = listener_match.group(1)
                listener_end = listener_match.end()

                # 查找listener之后的秘密揭示
                search_start = listener_end
                for secret_pattern in secret_patterns:
                    # 限制搜索范围在listener之后200字符内
                    search_region = text[search_start:search_start+200]
                    secret_match = re.search(secret_pattern, search_region)
                    if secret_match:
                        secret_text = secret_match.group()
                        secret_end = search_start + secret_match.end()

                        results.append({
                            "listener": listener,
                            "secret": secret_text[:50],  # 截断过长的描述
                            "after_text": text[secret_end:secret_end+100],  # 缩小窗口避免误判
                            "match_text": f"{listener_match.group()}{secret_text}"
                        })
                        break  # 找到一个秘密揭示就继续下一个listener

        # 也尝试直接匹配"告诉了X秘密"类型的模式
        direct_patterns = [
            r"告诉(\w+)关于(.+?)的秘密",
            r"向(\w+)透露(.+?)秘密",
            r"将(.+?)秘密告诉(\w+)",
        ]

        for pattern in direct_patterns:
            for m in re.finditer(pattern, text):
                groups = m.groups()
                if len(groups) >= 2:
                    # 交换listener和secret的位置
                    listener = groups[-1] if len(groups) > 1 else groups[0]
                    secret = groups[0] if len(groups) > 1 else "某个秘密"
                    end_pos = m.end()
                    results.append({
                        "listener": listener.strip(),
                        "secret": secret.strip()[:50],
                        "after_text": text[end_pos:end_pos+100],  # 缩小窗口避免误判
                        "match_text": m.group()
                    })

        # 模式3：告诉X "我的真实身份是..." 或类似模式（带中文引号）
        tell_pattern = r"告诉(\w+)[：:\"]"
        for m in re.finditer(tell_pattern, text):
            listener = m.group(1)
            end_pos = m.end()
            quote_region = text[end_pos:end_pos+200]
            # 支持中文引号「」""'' 和英文引号
            quote_match = re.search(r"[\"\"\"'']?(我的真实身份是|其实我是|我是)(.+?)[\"\"\"'']", quote_region)
            if quote_match:
                results.append({
                    "listener": listener,
                    "secret": quote_match.group()[:50],
                    "after_text": text[end_pos:end_pos+100],
                    "match_text": m.group() + quote_match.group()
                })

        return results

    def _shows_ignorance(self, text: str) -> bool:
        """检查是否表现出不知道"""
        for pattern in self.IGNORANCE_PATTERNS:
            if pattern in text:
                return True
        return False

    def _shows_acknowledgment(self, text: str) -> bool:
        """检查是否正确回应"""
        for pattern in self.ACKNOWLEDGMENT_PATTERNS:
            if pattern in text:
                return True
        return False

    def _create_issue(
        self,
        listener: str,
        secret: str,
        chapter_num: int,
        match_text: str
    ) -> Issue:
        return Issue(
            id=f"KT_{chapter_num:03d}_{listener[:10]}",
            severity=IssueSeverity.P1,
            checker_type=CheckerType.KNOWLEDGE_TRACKING,
            issue_type="knowledge_unacknowledged",
            title=f"信息未被确认: {listener}听到秘密却无反应",
            description=f"角色'{listener}'听到了关于'{secret}'的秘密，但没有表现出理解的迹象",
            location=IssueLocation(chapter=chapter_num),
            evidence=f"listener: {listener}, match: {match_text}",
            suggestion="需要加入角色回应（点头、明白了、原来如此等）"
        )
