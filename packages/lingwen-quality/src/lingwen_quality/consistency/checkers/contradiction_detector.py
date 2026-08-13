#!/usr/bin/env python3
"""
矛盾检测引擎

整合三大检测模式：
1. RuleBasedDetector - 规则匹配检测
2. AttributeComparer - 属性比对检测
3. LLMCausalReasoner - LLM推理检测

使用方式：
    detector = ContradictionDetector()
    contradictions = detector.detect_for_chapter(chapter_num, content, context)
    contradictions = detector.detect_all(chapters)
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from .attribute_comparer import AttributeComparer, AttributeValue
from .contradiction_detector_llm import LLMCausalReasoner
from .contradiction_detector_rules import RuleBasedDetector
from .contradiction_detector_types import ContradictionResult, DetectionConfig

logger = logging.getLogger(__name__)


class ContradictionDetector:
    """矛盾检测引擎

    整合三大检测模式，统一入口
    """

    def __init__(
        self,
        config: Optional[DetectionConfig] = None,
        llm_service=None,
    ):
        self.config = config or DetectionConfig()
        self.attribute_comparer = AttributeComparer()
        self.rule_detector = RuleBasedDetector()
        self.llm_reasoner = LLMCausalReasoner(llm_service)

        # 缓存
        self._chapter_cache: Dict[int, str] = {}
        self._all_attributes_cache: Optional[Dict[str, Dict[str, List[AttributeValue]]]] = None

    def detect_for_chapter(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ContradictionResult:
        """检测单章节矛盾"""
        import time
        start_time = time.perf_counter()

        context = context or {}
        contradictions = []

        # 更新缓存
        self._chapter_cache[chapter_num] = chapter_content

        # 1. 规则检测
        if self.config.enable_rule_based:
            previous_chapters = [
                (ch, content) for ch, content in self._chapter_cache.items()
                if ch < chapter_num
            ]
            rule_contradictions = self.rule_detector.detect(
                chapter_num, chapter_content, previous_chapters
            )
            contradictions.extend(rule_contradictions)

        # 2. 属性检测
        if self.config.enable_attribute:
            # 获取所有章节
            all_chapters = [
                (ch, content) for ch, content in sorted(self._chapter_cache.items())
            ]

            # 清除缓存的属性以重新计算
            self._all_attributes_cache = None

            # 提取并检测所有属性
            all_attributes = self.attribute_comparer.extract_all_attributes(
                all_chapters,
                self.config.attribute_types,
            )
            self._all_attributes_cache = all_attributes

            attribute_contradictions = self.attribute_comparer.detect_all_mismatches(
                all_attributes
            )
            contradictions.extend(attribute_contradictions)

        # 3. LLM检测（如果启用且有P1+问题）
        if self.config.enable_llm and contradictions:
            p1_contradictions = [c for c in contradictions if c.severity in ("P0", "P1")]
            if len(p1_contradictions) <= self.config.max_llm_cases:
                # 简化context用于LLM
                {
                    "related_chunks": context.get("related_chunks", []),
                }
                # 注意：LLM是异步的，这里简化处理
                # llm_contradictions = asyncio.run(self.llm_reasoner.detect(...))

        detection_time_ms = (time.perf_counter() - start_time) * 1000

        # 确定检测模式
        if self.config.enable_rule_based and self.config.enable_attribute:
            mode = "mixed"
        elif self.config.enable_attribute:
            mode = "attribute"
        else:
            mode = "rule_based"

        return ContradictionResult(
            chapter=chapter_num,
            contradictions=contradictions,
            detection_time_ms=detection_time_ms,
            detection_mode=mode,
            total_scanned=len(self._chapter_cache),
        )

    def detect_all(
        self,
        chapters: List[Tuple[int, str]],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ContradictionResult]:
        """全量检测所有章节"""
        results = []

        # 更新缓存
        for chapter_num, content in chapters:
            self._chapter_cache[chapter_num] = content

        # 批量属性检测（一次性提取所有属性）
        if self.config.enable_attribute:
            self._all_attributes_cache = self.attribute_comparer.extract_all_attributes(
                chapters,
                self.config.attribute_types,
            )

        # 逐章检测
        for chapter_num, content in sorted(chapters, key=lambda x: x[0]):
            result = self.detect_for_chapter(chapter_num, content, context)
            results.append(result)

        return results

    def get_contradiction_summary(
        self,
        results: List[ContradictionResult],
    ) -> Dict[str, Any]:
        """获取矛盾汇总统计"""
        all_contradictions = []
        for result in results:
            all_contradictions.extend(result.contradictions)

        # 按类型统计
        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {"P0": 0, "P1": 0, "P2": 0}
        by_entity: Dict[str, int] = {}

        for c in all_contradictions:
            by_type[c.contradiction_type] = by_type.get(c.contradiction_type, 0) + 1
            by_severity[c.severity] = by_severity.get(c.severity, 0) + 1
            if c.entity_name != "UNKNOWN" and c.entity_name != "LLM_DETECTED":
                by_entity[c.entity_name] = by_entity.get(c.entity_name, 0) + 1

        return {
            "total": len(all_contradictions),
            "by_type": by_type,
            "by_severity": by_severity,
            "by_entity": dict(sorted(by_entity.items(), key=lambda x: x[1], reverse=True)[:10]),
            "total_chapters": len(results),
            "chapters_with_issues": sum(1 for r in results if r.contradictions),
        }


# 导出（保留旧路径 API）
__all__ = [
    "ContradictionDetector",
    "ContradictionResult",
    "DetectionConfig",
    "RuleBasedDetector",
    "LLMCausalReasoner",
]