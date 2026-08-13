"""MasterController 工具函数

Phase 15.0 P3-SPLIT: 从 master_controller.py 拆分的工具函数。
"""
import math
import re

_NON_SAFE_LABEL_CHARS = re.compile(r"[^a-zA-Z0-9_]")


def _coerce_score(value, *, default=5):
    """把 LLM 返回的 score coerce + clamp 到 [0, 10] int 范围."""
    if value is None:
        return default
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(n):
        return default
    return max(0, min(10, round(n)))


def _safe_label(label):
    """把 label 规范成 JSON key 安全的 [a-zA-Z0-9_]+."""
    return _NON_SAFE_LABEL_CHARS.sub("_", label)