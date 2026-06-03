"""
质量检测与修复框架
提供Inspector和Repairer基类，以及YAML规则支持
"""

# Import 顺序至关重要:inspector/repairer 必须先于 checkers/repairers,
# 因为 checkers/repairers 内部 `from infra.quality import Inspector, Issue` 等。
# ruff 的 I001 自动 fix 会按字母排序破坏这个顺序(导致循环导入),
# 这里 noqa 锁定依赖方向。
from .inspector import Inspector, Issue, LLMBasedInspector, RuleBasedInspector  # noqa: I001
from .repairer import Repairer, RepairResult, RuleBasedRepairer, YAMLRuleRepairer  # noqa: I001
from .checkers import AITraceChecker, WorldviewChecker  # noqa: I001
from .repairers import AITraceRepairer, WorldviewRepairer  # noqa: I001

__all__ = [
    # Base classes
    "Inspector",
    "Issue",
    "RuleBasedInspector",
    "LLMBasedInspector",
    "Repairer",
    "RepairResult",
    "RuleBasedRepairer",
    "YAMLRuleRepairer",
    # Checkers
    "WorldviewChecker",
    "AITraceChecker",
    # Repairers
    "WorldviewRepairer",
    "AITraceRepairer",
]
