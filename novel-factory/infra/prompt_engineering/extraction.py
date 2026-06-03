"""灵文 LLM 抽取结果解析 (Phase 2.1)

Doc 1 §3.4 + Doc 2 §6 联动:解析 LLM 输出的 JSON,提取 ripple 信息。

核心 API:
- ExtractedRipple: 新涟漪 (待 RippleEngine.register)
- ExtractedResolution: 已平复 (待 RippleEngine.resolve)
- RippleExtractionResult: 完整结果
- parse_ripple_extraction(raw: str) → RippleExtractionResult
- ExtractionParseError: 解析失败 (非 JSON / 缺字段)

JSON 容忍:
- 纯 JSON: `{"new_ripples": [...], "resolved_ripples": [...]}`
- markdown 包装: ` ```json\\n{...}\\n``` ` (自动 strip)
- 周围文字: `以下是结果:\\n ```json ... ```\\n 其他` (提取 code block)

不导出 (后续阶段):
- 真实 LLM 调用 (Phase 2.12+)
- JSON schema 严格校验 (pydantic 等,Phase 3+)
- 流式解析 (Phase 3+)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


class ExtractionParseError(ValueError):
    """LLM 输出解析失败 (非 JSON / 缺字段 / 类型错误)"""


@dataclass(frozen=True)
class ExtractedRipple:
    """从 LLM 输出抽取的"新涟漪"

    Args:
        ripple_id: 简短 snake_case 标识
        origin_event: 事件描述 (10-50 字)
        origin_ch: 挖坑章节
        affected_nodes: 受影响角色/物品 ID 列表 (字符串,后续转换 NodeId)
        planned_resolve_ch: 计划平复章节 (LLM 估计)
        decay_rate: 衰减率 (Doc 1: 0.1-0.5)
    """

    ripple_id: str
    origin_event: str
    origin_ch: int
    affected_nodes: tuple[str, ...] = ()
    planned_resolve_ch: int | None = None
    decay_rate: float = 0.2


@dataclass(frozen=True)
class ExtractedResolution:
    """从 LLM 输出抽取的"已平复涟漪"

    Args:
        ripple_id: 目标 ripple_id (必须在 active_ripples 中)
        resolution_ch: 平复章节
        mode: 平复模式 (strong / weak / unresolved)
    """

    ripple_id: str
    resolution_ch: int
    mode: str  # "strong" | "weak" | "unresolved"


@dataclass(frozen=True)
class RippleExtractionResult:
    """LLM 抽取完整结果

    Args:
        new_ripples: 新涟漪 (待 register)
        resolved_ripples: 已平复 (待 resolve)
        notes: LLM 备注 (可选,供调试)
    """

    new_ripples: tuple[ExtractedRipple, ...] = ()
    resolved_ripples: tuple[ExtractedResolution, ...] = ()
    notes: str = ""


# ============ 核心 API ============

def parse_ripple_extraction(raw: str) -> RippleExtractionResult:
    """解析 LLM 输出 → RippleExtractionResult

    支持:
    - 纯 JSON
    - markdown ```json ... ``` 包装
    - 周围散文文字 (自动提取 code block)

    Raises:
        ExtractionParseError: 解析失败
    """
    if not raw or not raw.strip():
        raise ExtractionParseError("empty input")

    cleaned = _extract_json_block(raw)
    data = _parse_json(cleaned)
    return _build_result(data)


# ============ 内部 helpers ============

_CODE_BLOCK_RE = re.compile(
    r"```(?:json)?\s*\n?(.*?)\n?```",
    re.DOTALL,
)


def _extract_json_block(raw: str) -> str:
    """从 markdown 包装中提取 JSON,若无包装则返回原文本

    优先级:
    1. 寻找 ```json ... ``` 或 ``` ... ``` 代码块
    2. 否则返回原文本 (假设是纯 JSON)
    """
    match = _CODE_BLOCK_RE.search(raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


def _parse_json(text: str) -> dict[str, Any]:
    """解析 JSON 字符串 → dict

    Raises:
        ExtractionParseError: JSON 解析失败
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ExtractionParseError(
            f"invalid JSON at line {e.lineno} col {e.colno}: {e.msg}"
        ) from e
    if not isinstance(data, dict):
        raise ExtractionParseError(
            f"expected JSON object, got {type(data).__name__}"
        )
    return data


def _build_result(data: dict[str, Any]) -> RippleExtractionResult:
    """dict → RippleExtractionResult

    严格校验必需字段 (不 .get 兜底,缺则报错)
    """
    if "new_ripples" not in data:
        raise ExtractionParseError("missing required field: 'new_ripples'")
    if "resolved_ripples" not in data:
        raise ExtractionParseError("missing required field: 'resolved_ripples'")

    if not isinstance(data["new_ripples"], list):
        raise ExtractionParseError(
            f"'new_ripples' must be list, got {type(data['new_ripples']).__name__}"
        )
    if not isinstance(data["resolved_ripples"], list):
        raise ExtractionParseError(
            f"'resolved_ripples' must be list, got {type(data['resolved_ripples']).__name__}"
        )

    new_ripples = tuple(_parse_new_ripple(r) for r in data["new_ripples"])
    resolved_ripples = tuple(
        _parse_resolved_ripple(r) for r in data["resolved_ripples"]
    )
    notes = data.get("notes", "")
    if not isinstance(notes, str):
        notes = str(notes)

    return RippleExtractionResult(
        new_ripples=new_ripples,
        resolved_ripples=resolved_ripples,
        notes=notes,
    )


def _parse_new_ripple(raw: dict[str, Any]) -> ExtractedRipple:
    """dict → ExtractedRipple (严格校验)"""
    if not isinstance(raw, dict):
        raise ExtractionParseError(
            f"new_ripple must be dict, got {type(raw).__name__}"
        )
    # 必需字段
    for field_name in ("ripple_id", "origin_event", "origin_ch"):
        if field_name not in raw:
            raise ExtractionParseError(
                f"new_ripple missing required field: {field_name!r}"
            )

    # 类型校验
    if not isinstance(raw["ripple_id"], str):
        raise ExtractionParseError(
            f"ripple_id must be str, got {type(raw['ripple_id']).__name__}"
        )
    if not isinstance(raw["origin_event"], str):
        raise ExtractionParseError(
            f"origin_event must be str, got {type(raw['origin_event']).__name__}"
        )
    if not isinstance(raw["origin_ch"], int):
        raise ExtractionParseError(
            f"origin_ch must be int, got {type(raw['origin_ch']).__name__}"
        )

    # 可选字段
    affected = raw.get("affected_nodes", ())
    if not isinstance(affected, (list, tuple)):
        raise ExtractionParseError("affected_nodes must be list")
    planned = raw.get("planned_resolve_ch")
    decay = raw.get("decay_rate", 0.2)

    return ExtractedRipple(
        ripple_id=raw["ripple_id"],
        origin_event=raw["origin_event"],
        origin_ch=raw["origin_ch"],
        affected_nodes=tuple(affected),
        planned_resolve_ch=planned,
        decay_rate=float(decay),
    )


def _parse_resolved_ripple(raw: dict[str, Any]) -> ExtractedResolution:
    """dict → ExtractedResolution (严格校验)"""
    if not isinstance(raw, dict):
        raise ExtractionParseError(
            f"resolved_ripple must be dict, got {type(raw).__name__}"
        )
    for field_name in ("ripple_id", "resolution_ch", "mode"):
        if field_name not in raw:
            raise ExtractionParseError(
                f"resolved_ripple missing required field: {field_name!r}"
            )
    return ExtractedResolution(
        ripple_id=raw["ripple_id"],
        resolution_ch=int(raw["resolution_ch"]),
        mode=str(raw["mode"]),
    )


__all__ = [
    "ExtractedRipple",
    "ExtractedResolution",
    "RippleExtractionResult",
    "ExtractionParseError",
    "parse_ripple_extraction",
]
