"""
R2-011: 共享文本工具 — 消除 content.split('。') 在 5+ 处的重复
"""
from __future__ import annotations

from typing import List


def split_chinese_sentences(content: str) -> List[str]:
    """按中文句号(。)切分文本为句子列表

    行为与 str.split('。') 完全一致 — 唯一差别是单点修改:
    若以后要改为支持 ！？ 或过滤空串,只需改这一处。
    不在此过滤空串 — 现有 5 个调用方对空串都无害:
    - for s in sentences[-15:]  → 空串过 keyword 检查无命中
    - if len(sentences) < 3  → 空串计数不影响判断
    - sum/for 循环 → 空串对统计无贡献
    """
    return content.split('。')
