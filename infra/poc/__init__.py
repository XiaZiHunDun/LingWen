"""灵文 PoC (Phase 1.4 端到端集成验证)

PoC 范围 (per 计划):
- 1 main + 4 subplots × 5 chapters 端到端跑通
- 不调用真实 LLM (Mock compute_fn)
- 提供 scale_estimate 外推到 50 章
"""
from .run_volume_1 import (
    PoCResult,
    ScaleEstimate,
    build_test_world,
    run_poc,
    scale_estimate,
)

__all__ = [
    "run_poc",
    "build_test_world",
    "scale_estimate",
    "PoCResult",
    "ScaleEstimate",
]
