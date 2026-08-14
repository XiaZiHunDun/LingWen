"""检查器误报反馈机制

提供检查器反馈的收集、统计和查询功能，用于识别误报（false positive）
并优化检查器规则。

使用方式:
    from lingwen_quality.consistency.checker_feedback import (
        CheckerFeedback,
        record_feedback,
        get_false_positive_rate,
        get_checker_stats,
    )

    record_feedback("timeline_checker", "false_positive", 3, "时间线误报: 闪回场景")
    rate = get_false_positive_rate("timeline_checker")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from infra.errors import ValidationError

logger = logging.getLogger(__name__)

# ── 自定义异常 ──


class FeedbackError(ValidationError):
    """反馈记录错误"""


# ── 数据模型 ──


@dataclass
class FeedbackEntry:
    """单条反馈记录"""

    checker_id: str
    result_type: str  # "pass" | "fail" | "false_positive"
    chapter: int
    details: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ── 核心类 ──


class CheckerFeedback:
    """检查器反馈管理器（单例）

    追踪每个检查器的 pass/fail/false_positive 反馈，
    支持 JSON 文件持久化或纯内存模式。
    """

    _instance: CheckerFeedback | None = None

    def __new__(cls) -> CheckerFeedback:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._entries: list[FeedbackEntry] = []
        self._storage_path: str | None = None

    # ── 存储管理 ──

    def load_from_file(self, filepath: str) -> None:
        """从 JSON 文件加载反馈数据"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            logger.warning("反馈文件不存在: %s，使用空数据集", filepath)
            self._entries = []
            self._storage_path = filepath
            return
        except (json.JSONDecodeError, OSError) as e:
            raise FeedbackError(f"反馈文件加载失败: {e}") from e

        self._entries = []
        for item in raw:
            if isinstance(item, dict):
                self._entries.append(FeedbackEntry(
                    checker_id=item.get("checker_id", ""),
                    result_type=item.get("result_type", ""),
                    chapter=item.get("chapter", 0),
                    details=item.get("details", ""),
                    timestamp=item.get("timestamp", ""),
                ))
        self._storage_path = filepath
        logger.info("从 %s 加载了 %d 条反馈记录", filepath, len(self._entries))

    def save_to_file(self, filepath: str | None = None) -> None:
        """保存反馈数据到 JSON 文件"""
        target = filepath or self._storage_path
        if not target:
            raise FeedbackError("未指定存储路径，无法保存反馈数据")

        data = [
            {
                "checker_id": e.checker_id,
                "result_type": e.result_type,
                "chapter": e.chapter,
                "details": e.details,
                "timestamp": e.timestamp,
            }
            for e in self._entries
        ]
        import os
        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("反馈数据已保存至 %s（%d 条记录）", target, len(data))

    # ── 反馈记录 ──

    def record(self, checker_id: str, result_type: str, chapter: int, details: str = "") -> FeedbackEntry:
        """记录一条检查器反馈

        Args:
            checker_id: 检查器标识（如 "timeline_checker"）
            result_type: 结果类型（"pass" / "fail" / "false_positive"）
            chapter: 章节编号
            details: 详细信息（可选）

        Returns:
            新创建的 FeedbackEntry

        Raises:
            FeedbackError: result_type 无效时
        """
        valid_types = {"pass", "fail", "false_positive"}
        if result_type not in valid_types:
            raise FeedbackError(
                f"无效的 result_type: {result_type!r}，有效值: {valid_types}",
                suggestion=f"请使用 {valid_types} 中的值",
            )

        entry = FeedbackEntry(
            checker_id=checker_id,
            result_type=result_type,
            chapter=chapter,
            details=details,
        )
        self._entries.append(entry)
        logger.debug("记录反馈: checker=%s type=%s chapter=%d", checker_id, result_type, chapter)
        return entry

    # ── 统计查询 ──

    def get_false_positive_rate(self, checker_id: str) -> float:
        """获取指定检查器的误报率（百分比）

        Args:
            checker_id: 检查器标识

        Returns:
            误报率（0.0 ~ 100.0），无数据时返回 0.0
        """
        entries = [e for e in self._entries if e.checker_id == checker_id]
        if not entries:
            return 0.0

        fp_count = sum(1 for e in entries if e.result_type == "false_positive")
        total = len(entries)
        return round(fp_count / total * 100, 2)

    def get_checker_stats(self) -> dict[str, dict[str, Any]]:
        """获取所有检查器的统计数据

        Returns:
            {
                "checker_id": {
                    "total": int,
                    "pass": int,
                    "fail": int,
                    "false_positive": int,
                    "false_positive_rate": float,  # 百分比
                },
                ...
            }
        """
        stats: dict[str, dict[str, Any]] = {}
        for entry in self._entries:
            cid = entry.checker_id
            if cid not in stats:
                stats[cid] = {"total": 0, "pass": 0, "fail": 0, "false_positive": 0}
            stats[cid]["total"] += 1
            if entry.result_type in ("pass", "fail", "false_positive"):
                stats[cid][entry.result_type] += 1

        for cid in stats:
            s = stats[cid]
            s["false_positive_rate"] = round(
                s["false_positive"] / max(s["total"], 1) * 100, 2
            )

        return stats

    def get_all_entries(self) -> list[FeedbackEntry]:
        """返回所有反馈记录"""
        return list(self._entries)

    def clear(self) -> None:
        """清空所有反馈记录"""
        self._entries.clear()
        logger.info("反馈记录已清空")


# ── 模块级便捷函数 ──


def record_feedback(checker_id: str, result_type: str, chapter: int, details: str = "") -> FeedbackEntry:
    """记录一条检查器反馈（便捷函数）

    Args:
        checker_id: 检查器标识
        result_type: 结果类型（"pass" / "fail" / "false_positive"）
        chapter: 章节编号
        details: 详细信息

    Returns:
        新创建的 FeedbackEntry
    """
    return CheckerFeedback().record(checker_id, result_type, chapter, details)


def get_false_positive_rate(checker_id: str) -> float:
    """获取指定检查器的误报率（百分比）

    Args:
        checker_id: 检查器标识

    Returns:
        误报率（0.0 ~ 100.0）
    """
    return CheckerFeedback().get_false_positive_rate(checker_id)


def get_checker_stats() -> dict[str, dict[str, Any]]:
    """获取所有检查器的统计数据

    Returns:
        按 checker_id 分组的统计字典
    """
    return CheckerFeedback().get_checker_stats()


__all__ = [
    "CheckerFeedback",
    "FeedbackEntry",
    "FeedbackError",
    "record_feedback",
    "get_false_positive_rate",
    "get_checker_stats",
]