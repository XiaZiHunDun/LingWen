"""ContradictionDetector 公共数据类（拆分自 contradiction_detector.py）。

包含：
- ``ContradictionResult`` — 单章节矛盾检测汇总（含耗时/模式/总数）
- ``DetectionConfig`` — 检测器开关/阈值配置

下游消费者统一从 ``lingwen_quality.consistency.checkers.contradiction_detector``
导入（re-export），保持兼容性。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .attribute_comparer import Contradiction


@dataclass
class ContradictionResult:
    """矛盾检测结果"""
    chapter: int
    contradictions: List[Contradiction]
    detection_time_ms: float
    detection_mode: str  # rule_based / attribute / llm / mixed
    total_scanned: int = 0  # 扫描的实体数量

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter": self.chapter,
            "contradictions": [c.to_dict() for c in self.contradictions],
            "contradiction_count": len(self.contradictions),
            "detection_time_ms": self.detection_time_ms,
            "detection_mode": self.detection_mode,
            "total_scanned": self.total_scanned,
        }


@dataclass
class DetectionConfig:
    """检测配置"""
    enable_rule_based: bool = True
    enable_attribute: bool = True
    enable_llm: bool = False  # 默认关闭，LLM成本高
    llm_threshold: str = "P1"  # 只有P1+问题才启用LLM复核
    max_llm_cases: int = 10  # 最多复核10个案例
    attribute_types: List[str] = field(default_factory=lambda: ["年龄", "眼睛颜色", "头发颜色", "身高"])


__all__ = [
    "ContradictionResult",
    "DetectionConfig",
]