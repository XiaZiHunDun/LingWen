"""AI Tells 黑名单集成

检测文本中常见的 AI 写作套路化表达（AI Tells），帮助识别和降低
AI 生成内容的痕迹，提升写作风格的多样性和自然度。

使用方式:
    from infra.consistency.ai_tells_blacklist import (
        AI_TELLS_BLACKLIST,
        detect_ai_tells,
        get_style_diversity_score,
    )

    matches = detect_ai_tells("在这个充满危机的世界里，他不得不做出选择。")
    score = get_style_diversity_score(chapter_text)
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ── AI Tells 黑名单 ──
# 常见的 AI 写作套路化表达模式，检测到即标记

AI_TELLS_BLACKLIST: list[str] = [
    # 万能开头/结尾
    "在这个充满.*?的世界里",
    "在这个.*?的时代",
    "随着.*?的发展",

    # 冗余连接词
    "不禁",
    "不由得",
    "无可否认",
    "不可否认",
    "毫无疑问",
    "不言而喻",
    "众所周知",

    # 总结性套话
    "总而言之",
    "综上所述",
    "总的来看",
    "概括来说",
    "一言以蔽之",

    # 排比句式（AI 高频模式）
    "首先.*?其次.*?最后",
    "一方面.*?另一方面",
    "不仅.*?而且",
    "既.*?又",

    # 过程化表达
    "在.*?的过程中",
    "在.*?的进程中",
    "在这一刻",
    "在这一瞬间",

    # 强调/评价性套话
    "值得注意的是",
    "值得关注的是",
    "令人惊讶的是",
    "令人难以置信的是",
    "不可忽视的是",
    "需要指出的是",

    # 程度副词滥用
    "某种程度上",
    "某种意义上",
    "在一定程度上",
    "从某种角度来说",

    # 万能转折
    "然而，(?:事情|情况|事实|一切).*?并非如此",
    "但(?:事情|情况|事实|一切).*?并非如此",

    # 万能描写
    "他的眼神中.*?闪过一丝",
    "她的眼神中.*?闪过一丝",
    "心中涌起.*?一股",
    "嘴角.*?微微.*?上扬",
    "目光.*?深邃",
    "他的声音.*?低沉.*?而",
    "她的声音.*?温柔.*?而",

    # 万能情感描述
    "心中充满了",
    "内心充满了",
    "一种难以言喻的",
    "一种说不出的",
    "复杂的情绪",
    "复杂的情感",
]


# ── 编译正则表达式 ──

def _compile_patterns() -> list[tuple[str, re.Pattern[str]]]:
    """将黑名单模式编译为正则表达式"""
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for pattern in AI_TELLS_BLACKLIST:
        try:
            compiled.append((pattern, re.compile(pattern, re.IGNORECASE)))
        except re.error as e:
            logger.warning("AI Tells 模式编译失败: %r — %s", pattern, e)
    return compiled


_COMPILED_PATTERNS: list[tuple[str, re.Pattern[str]]] = _compile_patterns()


# ── 检测函数 ──


def detect_ai_tells(text: str) -> list[dict[str, Any]]:
    """扫描文本，检测 AI 写作套路化表达

    Args:
        text: 待检测的文本

    Returns:
        [{"pattern": str, "match": str, "start": int, "end": int}, ...]
        匹配列表，按位置排序
    """
    if not text or not text.strip():
        return []

    matches: list[dict[str, Any]] = []
    seen_spans: set[tuple[int, int]] = set()

    for pattern_str, compiled in _COMPILED_PATTERNS:
        for m in compiled.finditer(text):
            span = (m.start(), m.end())
            # 去重：同一位置不重复标记
            if span in seen_spans:
                continue
            seen_spans.add(span)
            matches.append({
                "pattern": pattern_str,
                "match": m.group(),
                "start": m.start(),
                "end": m.end(),
            })

    # 按位置排序
    matches.sort(key=lambda x: x["start"])
    return matches


def get_style_diversity_score(text: str) -> float:
    """估算写作风格的多样性得分（0.0 ~ 1.0）

    基于以下因素计算：
    - AI Tells 命中率（越低越好）
    - 句子长度方差（越大越好）
    - 段落结构多样性

    Args:
        text: 待评估的文本

    Returns:
        风格多样性得分（0.0 = 高度套路化，1.0 = 高度多样化）
    """
    if not text or not text.strip():
        return 1.0

    # 1. AI Tells 命中率
    matches = detect_ai_tells(text)
    # 按每 1000 字计算命中密度
    char_count = len(text)
    tell_density = len(matches) / max(char_count / 1000, 0.001)
    # 命中密度越高，得分越低（0 命中 = 1.0，>= 5 命中/千字 = 0.0）
    tell_score = max(0.0, 1.0 - tell_density / 5.0)

    # 2. 句子长度方差
    sentences = _extract_sentences(text)
    if len(sentences) >= 3:
        lengths = [len(s) for s in sentences]
        avg_len = sum(lengths) / len(lengths)
        variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
        # 方差归一化：方差 >= 1000 视为满分
        variance_score = min(1.0, variance / 1000.0)
    else:
        variance_score = 0.5

    # 3. 综合得分
    # AI Tells 权重 0.6，句子方差权重 0.4
    score = tell_score * 0.6 + variance_score * 0.4
    return round(min(1.0, max(0.0, score)), 2)


def _extract_sentences(text: str) -> list[str]:
    """从文本中提取句子列表"""
    # 使用中文标点分割句子
    raw = re.split(r"[。！？!?\n]+", text)
    return [s.strip() for s in raw if s.strip() and len(s.strip()) >= 2]


def get_ai_tell_summary(text: str) -> dict[str, Any]:
    """获取文本的 AI Tells 摘要

    Args:
        text: 待检测的文本

    Returns:
        {
            "total_matches": int,
            "unique_patterns": int,
            "match_details": list[dict],
            "style_diversity_score": float,
        }
    """
    matches = detect_ai_tells(text)
    unique_patterns = len({m["pattern"] for m in matches})

    return {
        "total_matches": len(matches),
        "unique_patterns": unique_patterns,
        "match_details": matches,
        "style_diversity_score": get_style_diversity_score(text),
    }


__all__ = [
    "AI_TELLS_BLACKLIST",
    "detect_ai_tells",
    "get_style_diversity_score",
    "get_ai_tell_summary",
]