"""
Reader Feedback Classifier

Maps reader feedback to P0/P1/P2 severity levels for proper triage and resolution.
"""

import re
from typing import Tuple

# P0 keywords: Plot breaks, character death inconsistencies, timeline contradictions,
# core world-building contradictions
P0_PATTERNS = [
    # Plot breaks and contradictions
    (r"前后矛盾", "logic_inconsistency"),
    (r"自相矛盾", "logic_inconsistency"),
    (r"逻辑硬伤", "logic_inconsistency"),
    (r"根本讲不通", "logic_inconsistency"),
    (r"完全不成立", "logic_inconsistency"),
    # Timeline contradictions
    (r"时间线.*矛盾", "logic_inconsistency"),
    (r"时间.*对不上", "logic_inconsistency"),
    (r"前面.*后面.*不一致", "logic_inconsistency"),
    # Character death inconsistencies
    (r"死了.*又活了", "logic_inconsistency"),
    (r"死而复生", "logic_inconsistency"),
    (r"死得不明不白", "logic_inconsistency"),
    # Core world-building contradictions
    (r"世界观.*矛盾", "logic_inconsistency"),
    (r"设定.*冲突", "logic_inconsistency"),
    (r"力量体系.*崩塌", "logic_inconsistency"),
    (r"设定.*崩溃", "logic_inconsistency"),
    # Major plot invalidation
    (r"主线.*废了", "logic_inconsistency"),
    (r"剧情.*无法自圆其说", "logic_inconsistency"),
    (r"整个故事.*不成立", "logic_inconsistency"),
    # Factual errors that invalidate plot
    (r"事实错误", "logic_inconsistency"),
    (r"专业领域.*错误", "logic_inconsistency"),
]

# P1 keywords: Character behavior inconsistent, logical gaps in scene transitions,
# missing foreshadow payoffs, unfulfilled emotional expectations
P1_PATTERNS = [
    # Character behavior inconsistent with established personality
    (r"人设.*崩", "character_behavior"),
    (r"人设崩塌", "character_behavior"),
    (r"性格.*变了", "character_behavior"),
    (r"行为.*不合理", "character_behavior"),
    (r"角色.*突然.*降智", "character_behavior"),
    (r"主角.*突然变蠢", "character_behavior"),
    (r"配角.*无脑", "character_behavior"),
    # Logical gaps in scene transitions
    (r"过渡.*不自然", "plot_hole"),
    (r"转场.*突兀", "plot_hole"),
    (r"场景.*跳跃.*太大", "plot_hole"),
    (r"情节.*跳跃", "plot_hole"),
    (r"突然就.*了", "plot_hole"),
    # Missing foreshadow payoffs
    (r"伏笔.*没回收", "plot_hole"),
    (r"伏笔.*没交代", "plot_hole"),
    (r"前面.*后面.*没呼应", "plot_hole"),
    (r"埋的.*坑.*没填", "plot_hole"),
    (r"悬念.*没了下文", "plot_hole"),
    # Unfulfilled emotional expectations
    (r"感情.*不到位", "emotional_disconnect"),
    (r"情绪.*不够", "emotional_disconnect"),
    (r"感动.*不了", "emotional_disconnect"),
    (r"情绪调动.*失败", "emotional_disconnect"),
    (r"情感共鸣.*缺失", "emotional_disconnect"),
    (r"期待.*落空", "emotional_disconnect"),
    (r"高潮.*没起来", "emotional_disconnect"),
]

# P2 keywords: Style inconsistencies, minor pacing issues,
# minor emotional resonance gaps, repetitive sentence patterns
P2_PATTERNS = [
    # Style inconsistencies
    (r"文笔.*不一致", "style_issue"),
    (r"风格.*突变", "style_issue"),
    (r"笔触.*不一样", "style_issue"),
    (r"描写.*风格.*不统一", "style_issue"),
    # Minor pacing issues
    (r"节奏.*有点.*拖", "pacing_issue"),
    (r"节奏.*偏慢", "pacing_issue"),
    (r"节奏.*太快", "pacing_issue"),
    (r"节奏把控.*不够好", "pacing_issue"),
    (r"进展.*太慢", "pacing_issue"),
    (r"进展.*太快.*来不及.*反应", "pacing_issue"),
    # Minor emotional resonance gaps
    (r"情感.*略显平淡", "emotional_disconnect"),
    (r"情绪.*差一点", "emotional_disconnect"),
    (r"共鸣.*不够强", "emotional_disconnect"),
    (r"感动.*差一点", "emotional_disconnect"),
    # Repetitive sentence patterns
    (r"句式.*重复", "style_issue"),
    (r"表达.*单调", "style_issue"),
    (r"用词.*重复", "style_issue"),
    (r"形容.*重复", "style_issue"),
    (r"词汇.*贫乏", "style_issue"),
    (r"同一个词.*用太多", "style_issue"),
    (r"模板句", "style_issue"),
    # Readability
    (r"病句.*错字", "style_issue"),
    (r"语句.*不通顺", "style_issue"),
    (r"读起来.*别扭", "style_issue"),
    (r"可读性.*差", "style_issue"),
]


def classify_reader_feedback(feedback_text: str) -> Tuple[str, int, str]:
    """
    Classify reader feedback into issue type and P0/P1/P2 severity.

    Args:
        feedback_text: The reader feedback text (in Chinese)

    Returns:
        Tuple of (issue_type, severity, reasoning)
        - issue_type: logic_inconsistency, character_behavior, plot_hole,
                     style_issue, emotional_disconnect, pacing_issue, other
        - severity: P0, P1, or P2 (returned as int: 0, 1, or 2)
        - reasoning: Explanation of the classification
    """
    if not feedback_text or not feedback_text.strip():
        return ("other", 2, "Empty feedback, classified as P2 other")

    text = feedback_text.strip()

    # Check P0 patterns first (highest priority)
    for pattern, issue_type in P0_PATTERNS:
        if re.search(pattern, text):
            severity = 0
            return (issue_type, severity, f"P0 detected: pattern '{pattern}' matched - severe logic inconsistency that invalidates major plot points")

    # Check P1 patterns
    for pattern, issue_type in P1_PATTERNS:
        if re.search(pattern, text):
            severity = 1
            return (issue_type, severity, f"P1 detected: pattern '{pattern}' matched - character behavior or plot hole issue")

    # Check P2 patterns
    for pattern, issue_type in P2_PATTERNS:
        if re.search(pattern, text):
            severity = 2
            return (issue_type, severity, f"P2 detected: pattern '{pattern}' matched - style or pacing issue")

    # Default: no specific pattern matched, classify as P2 other
    return ("other", 2, "No specific pattern matched - classified as P2 other for minor review")


def get_severity_label(severity: int) -> str:
    """Convert severity int to label string."""
    labels = {0: "P0", 1: "P1", 2: "P2"}
    return labels.get(severity, "P2")


if __name__ == "__main__":
    # Demo usage
    examples = [
        "这段情节完全讲不通，前面说主角已经死了，后面又说他在跟别人聊天，这是前后矛盾",
        "主角性格突然变了，之前是个聪明人，这里突然降智做傻事",
        "这段对话文笔不一致，前面很优美，后面突然变得很口语化",
        "节奏有点拖沓，进展太慢，看得有点无聊",
        "词汇有点贫乏，同一个词用太多了",
    ]

    for feedback in examples:
        issue_type, severity, reasoning = classify_reader_feedback(feedback)
        print(f"Feedback: {feedback[:50]}...")
        print(f"  Type: {issue_type}, Severity: {get_severity_label(severity)}")
        print(f"  Reasoning: {reasoning}\n")
