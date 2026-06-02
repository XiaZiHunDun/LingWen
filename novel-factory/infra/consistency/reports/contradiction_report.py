#!/usr/bin/env python3
"""
矛盾报告生成器

生成结构化矛盾报告，包含分类统计、严重程度评估、修复建议

使用方式：
    report_gen = ContradictionReporter()
    report = report_gen.generate(chapter_num, contradictions)
    print(report.format_text())
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from infra.consistency.checkers.attribute_comparer import Contradiction


@dataclass
class ContradictionReport:
    """矛盾报告"""
    chapter: int
    generated_at: datetime = field(default_factory=datetime.now)
    contradictions: List[Contradiction] = field(default_factory=list)
    total_count: int = 0
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0

    # 统计信息
    by_type: Dict[str, int] = field(default_factory=dict)
    by_entity: Dict[str, int] = field(default_factory=dict)

    # 元数据
    detection_mode: str = ""
    detection_time_ms: float = 0.0

    def __post_init__(self):
        self.total_count = len(self.contradictions)
        self.p0_count = sum(1 for c in self.contradictions if c.severity == "P0")
        self.p1_count = sum(1 for c in self.contradictions if c.severity == "P1")
        self.p2_count = sum(1 for c in self.contradictions if c.severity == "P2")

        # 按类型统计
        for c in self.contradictions:
            self.by_type[c.contradiction_type] = self.by_type.get(c.contradiction_type, 0) + 1

        # 按实体统计
        for c in self.contradictions:
            if c.entity_name not in ("UNKNOWN", "LLM_DETECTED"):
                self.by_entity[c.entity_name] = self.by_entity.get(c.entity_name, 0) + 1

    def format_text(self) -> str:
        """格式化文本报告"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"矛盾检测报告 - 第{self.chapter}章")
        lines.append("=" * 60)
        lines.append(f"生成时间: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"检测模式: {self.detection_mode}")
        lines.append(f"检测耗时: {self.detection_time_ms:.2f}ms")
        lines.append("")

        # 汇总统计
        lines.append("【汇总统计】")
        lines.append(f"  总矛盾数: {self.total_count}")
        lines.append(f"  P0(致命): {self.p0_count}")
        lines.append(f"  P1(严重): {self.p1_count}")
        lines.append(f"  P2(中等): {self.p2_count}")
        lines.append("")

        # 按类型分布
        if self.by_type:
            lines.append("【按类型分布】")
            for type_name, count in sorted(self.by_type.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {type_name}: {count}")
            lines.append("")

        # 按实体分布
        if self.by_entity:
            lines.append("【涉及实体】")
            for entity, count in sorted(self.by_entity.items(), key=lambda x: x[1], reverse=True)[:10]:
                lines.append(f"  {entity}: {count}处")
            lines.append("")

        # 详细矛盾列表
        if self.contradictions:
            lines.append("【详细矛盾】")
            for i, c in enumerate(self.contradictions, 1):
                lines.append(f"\n--- 矛盾 {i} ---")
                lines.append(f"  类型: {c.contradiction_type}")
                lines.append(f"  严重程度: {c.severity}")
                if c.entity_name not in ("UNKNOWN", "LLM_DETECTED"):
                    lines.append(f"  涉及实体: {c.entity_name}")
                lines.append(f"  描述: {c.description}")
                if c.values:
                    lines.append("  证据:")
                    for v in c.values:
                        lines.append(f"    - ch{v.chapter}: {v.value}")
                lines.append(f"  建议: {c.suggestion}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def format_json(self) -> str:
        """格式化JSON报告"""
        return json.dumps({
            "chapter": self.chapter,
            "generated_at": self.generated_at.isoformat(),
            "summary": {
                "total": self.total_count,
                "p0": self.p0_count,
                "p1": self.p1_count,
                "p2": self.p2_count,
            },
            "by_type": self.by_type,
            "by_entity": self.by_entity,
            "detection_mode": self.detection_mode,
            "detection_time_ms": self.detection_time_ms,
            "contradictions": [c.to_dict() for c in self.contradictions],
        }, ensure_ascii=False, indent=2)

    def format_markdown(self) -> str:
        """格式化Markdown报告"""
        lines = []
        lines.append(f"# 矛盾检测报告 - 第{self.chapter}章")
        lines.append("")
        lines.append(f"**生成时间**: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**检测模式**: {self.detection_mode}")
        lines.append(f"**检测耗时**: {self.detection_time_ms:.2f}ms")
        lines.append("")

        # 汇总表格
        lines.append("## 汇总统计")
        lines.append("")
        lines.append("| 级别 | 数量 |")
        lines.append("|------|------|")
        lines.append(f"| P0(致命) | {self.p0_count} |")
        lines.append(f"| P1(严重) | {self.p1_count} |")
        lines.append(f"| P2(中等) | {self.p2_count} |")
        lines.append(f"| **总计** | **{self.total_count}** |")
        lines.append("")

        # 按类型分布
        if self.by_type:
            lines.append("## 按类型分布")
            lines.append("")
            lines.append("| 类型 | 数量 |")
            lines.append("|------|------|")
            for type_name, count in sorted(self.by_type.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| {type_name} | {count} |")
            lines.append("")

        # 按实体分布
        if self.by_entity:
            lines.append("## 涉及实体 (Top 10)")
            lines.append("")
            lines.append("| 实体 | 矛盾数 |")
            lines.append("|------|--------|")
            for entity, count in sorted(self.by_entity.items(), key=lambda x: x[1], reverse=True)[:10]:
                lines.append(f"| {entity} | {count} |")
            lines.append("")

        # 详细矛盾列表
        if self.contradictions:
            lines.append("## 详细矛盾")
            lines.append("")
            for i, c in enumerate(self.contradictions, 1):
                severity_icon = {"P0": "🔴", "P1": "🟡", "P2": "🟢"}.get(c.severity, "⚪")
                lines.append(f"### {severity_icon} 矛盾 {i}: {c.contradiction_type}")
                lines.append("")
                lines.append(f"**严重程度**: {c.severity}")
                if c.entity_name not in ("UNKNOWN", "LLM_DETECTED"):
                    lines.append(f"**涉及实体**: {c.entity_name}")
                lines.append("")
                lines.append(f"**描述**: {c.description}")
                lines.append("")
                if c.values:
                    lines.append("**证据**:")
                    lines.append("```")
                    for v in c.values:
                        lines.append(f"第{v.chapter}章: {v.value}")
                    lines.append("```")
                    lines.append("")
                lines.append(f"**建议**: {c.suggestion}")
                lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chapter": self.chapter,
            "generated_at": self.generated_at.isoformat(),
            "summary": {
                "total": self.total_count,
                "p0": self.p0_count,
                "p1": self.p1_count,
                "p2": self.p2_count,
            },
            "by_type": self.by_type,
            "by_entity": self.by_entity,
            "detection_mode": self.detection_mode,
            "detection_time_ms": self.detection_time_ms,
            "contradictions": [c.to_dict() for c in self.contradictions],
        }


class ContradictionReporter:
    """矛盾报告生成器"""

    def __init__(self):
        pass

    def generate(
        self,
        chapter: int,
        contradictions: List[Contradiction],
        detection_mode: str = "",
        detection_time_ms: float = 0.0,
    ) -> ContradictionReport:
        """生成单章报告"""
        return ContradictionReport(
            chapter=chapter,
            contradictions=contradictions,
            detection_mode=detection_mode,
            detection_time_ms=detection_time_ms,
        )

    def generate_batch(
        self,
        results: List[Any],  # List[ContradictionResult]
    ) -> Dict[int, ContradictionReport]:
        """批量生成报告"""
        reports = {}
        for result in results:
            report = self.generate(
                chapter=result.chapter,
                contradictions=result.contradictions,
                detection_mode=result.detection_mode,
                detection_time_ms=result.detection_time_ms,
            )
            reports[result.chapter] = report
        return reports

    def generate_summary(
        self,
        reports: Dict[int, ContradictionReport],
    ) -> Dict[str, Any]:
        """生成汇总报告"""
        all_contradictions = []
        for report in reports.values():
            all_contradictions.extend(report.contradictions)

        # 全局统计
        total_p0 = sum(r.p0_count for r in reports.values())
        total_p1 = sum(r.p1_count for r in reports.values())
        total_p2 = sum(r.p2_count for r in reports.values())

        # 按类型汇总
        by_type: Dict[str, int] = {}
        for report in reports.values():
            for type_name, count in report.by_type.items():
                by_type[type_name] = by_type.get(type_name, 0) + count

        # 按实体汇总
        by_entity: Dict[str, int] = {}
        for report in reports.values():
            for entity, count in report.by_entity.items():
                by_entity[entity] = by_entity.get(entity, 0) + count

        return {
            "total_chapters": len(reports),
            "chapters_with_issues": sum(1 for r in reports.values() if r.total_count > 0),
            "summary": {
                "total_contradictions": len(all_contradictions),
                "p0": total_p0,
                "p1": total_p1,
                "p2": total_p2,
            },
            "by_type": by_type,
            "top_entities": dict(sorted(by_entity.items(), key=lambda x: x[1], reverse=True)[:20]),
        }


# 导出
__all__ = ["ContradictionReporter", "ContradictionReport"]
