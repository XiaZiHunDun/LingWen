#!/usr/bin/env python3
"""
检查器自检器 - Layer 5 实现
追踪每个检查器的误报率，自动调整灵敏度或建议加入白名单
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONTEXT_DIR = PROJECT_ROOT / "context"
PERFORMANCE_PATH = CONTEXT_DIR / "checker_performance.json"

# 误报率阈值
FALSE_POSITIVE_RATE_THRESHOLD = 0.3  # 30% 误报率阈值
CONFIDENCE_WEIGHT_THRESHOLD = 0.6   # 置信度权重阈值


@dataclass
class InspectionResult:
    """自检结果"""
    checker_type: str
    false_positive_rate: float
    avg_confidence_score: float
    total_issues: int
    recommendations: List[str]  # 建议列表
    should_auto_fix: bool      # 是否应自动修复


class CheckerInspector:
    """检查器自检器（单例）"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.performance_data = self._load_performance()

    def _load_performance(self) -> Dict[str, Any]:
        """加载性能数据"""
        if not PERFORMANCE_PATH.exists():
            return self._default_performance()
        try:
            with open(PERFORMANCE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return self._default_performance()

    def _default_performance(self) -> Dict[str, Any]:
        return {
            "checkers": {},
            "last_full_inspection": None,
            "auto_fix_enabled": True
        }

    def _save_performance(self):
        """保存性能数据"""
        PERFORMANCE_PATH.parent.mkdir(exist_ok=True)
        with open(PERFORMANCE_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.performance_data, f, ensure_ascii=False, indent=2)

    def record_issue_result(self, checker_type: str, is_false_positive: bool, confidence_score: float = 0.5):
        """记录检测结果"""
        if checker_type not in self.performance_data["checkers"]:
            self.performance_data["checkers"][checker_type] = {
                "total_detections": 0,
                "false_positive_count": 0,
                "true_positive_count": 0,
                "false_positive_rate": 0.0,
                "avg_confidence_score": 0.5,
                "last_updated": None
            }

        stats = self.performance_data["checkers"][checker_type]
        stats["total_detections"] += 1
        if is_false_positive:
            stats["false_positive_count"] += 1
        else:
            stats["true_positive_count"] += 1

        # 更新误报率
        total = stats["total_detections"]
        fp = stats["false_positive_count"]
        stats["false_positive_rate"] = fp / max(total, 1)

        # 更新平均置信度
        prev_avg = stats.get("avg_confidence_score", 0.5)
        stats["avg_confidence_score"] = (prev_avg * (total - 1) + confidence_score) / total
        stats["last_updated"] = datetime.now().isoformat()

        self._save_performance()

    def get_checker_stats(self, checker_type: str) -> Dict[str, Any]:
        """获取检查器统计"""
        return self.performance_data["checkers"].get(checker_type, {})

    def inspect_checker(self, checker_type: str) -> InspectionResult:
        """检查单个检查器的性能"""
        stats = self.get_checker_stats(checker_type)
        if not stats or stats.get("total_detections", 0) == 0:
            return InspectionResult(
                checker_type=checker_type,
                false_positive_rate=0.0,
                avg_confidence_score=0.5,
                total_issues=0,
                recommendations=["无数据"],
                should_auto_fix=False
            )

        fp_rate = stats.get("false_positive_rate", 0.0)
        avg_confidence = stats.get("avg_confidence_score", 0.5)
        total = stats.get("total_detections", 0)

        recommendations = []
        should_auto_fix = False

        # 检查误报率阈值
        if fp_rate > FALSE_POSITIVE_RATE_THRESHOLD:
            recommendations.append(f"误报率 {fp_rate:.1%} 超过阈值 {FALSE_POSITIVE_RATE_THRESHOLD:.1%}，建议加入白名单")
            should_auto_fix = True

        # 检查置信度分数
        if avg_confidence < CONFIDENCE_WEIGHT_THRESHOLD:
            recommendations.append(f"平均置信度 {avg_confidence:.2f} 低于阈值 {CONFIDENCE_WEIGHT_THRESHOLD:.2f}，降低灵敏度")

        # 检查绝对数量
        if stats.get("false_positive_count", 0) > 10:
            recommendations.append(f"误报数量 {stats['false_positive_count']} 超过10，建议人工审核")

        return InspectionResult(
            checker_type=checker_type,
            false_positive_rate=fp_rate,
            avg_confidence_score=avg_confidence,
            total_issues=total,
            recommendations=recommendations,
            should_auto_fix=should_auto_fix
        )

    def inspect_all_checkers(self) -> List[InspectionResult]:
        """检查所有检查器"""
        results = []
        for checker_type in self.performance_data["checkers"]:
            result = self.inspect_checker(checker_type)
            results.append(result)

        self.performance_data["last_full_inspection"] = datetime.now().isoformat()
        self._save_performance()
        return results

    def get_auto_fix_recommendations(self) -> List[Dict[str, Any]]:
        """获取自动修复建议（用于更新白名单）"""
        recommendations = []
        for result in self.inspect_all_checkers():
            if result.should_auto_fix:
                recommendations.append({
                    "checker_type": result.checker_type,
                    "false_positive_rate": result.false_positive_rate,
                    "recommendations": result.recommendations
                })
        return recommendations