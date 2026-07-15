"""灵文快照差异 (Phase 2.6 — SnapshotDiff)

Doc 1 §3.4 + Doc 3 联动: 比较两个 WorldSnapshot, 返回 5 类别 (NODE / RELATION
/ RIPPLE / SUBPLOT / MOOD) + 2 delta (PHYSICAL / MENTAL) 的变化列表。

5 类别 ADDED/REMOVED/MODIFIED 判定:
- NODE: 主键 str(NodeId), 字典差
- RELATION: 主键 "src→dst" 字符串
- RIPPLE: 主键 ripple_id, state 变化 → MODIFIED + field_changes
- SUBPLOT: 主键 plot_id, status 变化 → MODIFIED + field_changes
- MOOD: 单一字段, 变 → MODIFIED + field_changes=(("value", prev, curr),)

2 delta:
- PHYSICAL: 比较 ch / state 元组, 变 → MODIFIED
- MENTAL: 同上

不导出 (后续阶段):
- 跨卷快照聚合 (Phase 3+)
- LLM 解释 diff (Phase 2+)
- diff 性能优化 (>1000 chapter 场景)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from infra.world_model.data_structures import WorldSnapshot


class ChangeKind(str, Enum):
    """变化类型"""

    ADDED = "added"        # prev 不存在, curr 存在
    REMOVED = "removed"    # prev 存在, curr 不存在
    MODIFIED = "modified"  # 两边都存在但字段不同


class EntityKind(str, Enum):
    """变化实体类别"""

    NODE = "node"
    RELATION = "relation"
    RIPPLE = "ripple"
    SUBPLOT = "subplot"
    MOOD = "mood"
    PHYSICAL = "physical_line"
    MENTAL = "mental_line"


@dataclass(frozen=True)
class SnapshotChange:
    """单个变化单元

    Args:
        kind: ADDED / REMOVED / MODIFIED
        entity: 实体类别
        entity_id: 主键 (e.g. ripple_id, str(NodeId), "src→dst", "world_mood")
        before: 旧值 (ADDED 时为 None,REMOVED 时有值,MODIFIED 时为 prev)
        after: 新值 (ADDED 时有值,REMOVED 时为 None,MODIFIED 时为 curr)
        field_changes: 字段级变化 (field_name, before, after) 元组
    """

    kind: ChangeKind
    entity: EntityKind
    entity_id: str
    before: Any = None
    after: Any = None
    field_changes: tuple[tuple[str, Any, Any], ...] = ()


# ============ 主入口 ============

def diff_snapshots(
    prev: WorldSnapshot, curr: WorldSnapshot
) -> tuple[SnapshotChange, ...]:
    """主入口: 返回 7 类别变化 (5 实体 + 2 delta)"""
    return (
        *_diff_nodes(prev, curr),
        *_diff_relations(prev, curr),
        *diff_ripples(prev, curr),
        *diff_subplots(prev, curr),
        *_diff_mood(prev, curr),
        *_diff_physical(prev, curr),
        *_diff_mental(prev, curr),
    )


# ============ 单独导出 (常用) ============

def diff_ripples(
    prev: WorldSnapshot, curr: WorldSnapshot
) -> tuple[SnapshotChange, ...]:
    """仅 ripple 类别 diff (state 变化 + wavefront 增删)"""
    prev_rips = {r.ripple_id: r for r in prev.active_ripples}
    curr_rips = {r.ripple_id: r for r in curr.active_ripples}
    return _diff_entity_set(
        prev_rips, curr_rips, EntityKind.RIPPLE,
        field_names=("state", "wavefront", "planned_resolve_ch", "resolved_ch",
                     "decay_rate", "affected_nodes", "affected_relations"),
    )


def diff_subplots(
    prev: WorldSnapshot, curr: WorldSnapshot
) -> tuple[SnapshotChange, ...]:
    """仅 subplot 类别 diff (status 变化)"""
    prev_plots = {_plot_key(p): p for p in prev.active_subplots}
    curr_plots = {_plot_key(p): p for p in curr.active_subplots}
    return _diff_entity_set(
        prev_plots, curr_plots, EntityKind.SUBPLOT,
        field_names=("status", "close_ch", "active_ch_range", "related_ripples"),
    )


def has_state_transition(
    changes: tuple[SnapshotChange, ...],
    ripple_id: str,
    from_state: Any,
    to_state: Any,
) -> bool:
    """便捷查询: ripple 是否在 changes 中发生 from_state → to_state 转换"""
    for c in changes:
        if (
            c.entity == EntityKind.RIPPLE
            and c.entity_id == ripple_id
            and c.kind == ChangeKind.MODIFIED
        ):
            for field, before, after in c.field_changes:
                if field == "state" and before == from_state and after == to_state:
                    return True
    return False


# ============ 内部 helpers ============

def _diff_nodes(
    prev: WorldSnapshot, curr: WorldSnapshot
) -> tuple[SnapshotChange, ...]:
    prev_keys = {str(k): k for k in prev.nodes}
    curr_keys = {str(k): k for k in curr.nodes}
    changes: list[SnapshotChange] = []

    # ADDED
    for k_str, k_obj in curr_keys.items():
        if k_str not in prev_keys:
            changes.append(
                SnapshotChange(
                    kind=ChangeKind.ADDED,
                    entity=EntityKind.NODE,
                    entity_id=k_str,
                    after=curr.nodes[k_obj],
                )
            )
    # REMOVED
    for k_str, k_obj in prev_keys.items():
        if k_str not in curr_keys:
            changes.append(
                SnapshotChange(
                    kind=ChangeKind.REMOVED,
                    entity=EntityKind.NODE,
                    entity_id=k_str,
                    before=prev.nodes[k_obj],
                )
            )
    # MODIFIED (KeyPoint 字段变化)
    for k_str in prev_keys.keys() & curr_keys.keys():
        prev_kp = prev.nodes[prev_keys[k_str]]
        curr_kp = curr.nodes[curr_keys[k_str]]
        field_changes = _diff_fields(
            prev_kp, curr_kp,
            fields=("description", "stability", "first_ch", "last_ch", "tags"),
        )
        if field_changes:
            changes.append(
                SnapshotChange(
                    kind=ChangeKind.MODIFIED,
                    entity=EntityKind.NODE,
                    entity_id=k_str,
                    before=prev_kp,
                    after=curr_kp,
                    field_changes=field_changes,
                )
            )
    return tuple(changes)


def _diff_relations(
    prev: WorldSnapshot, curr: WorldSnapshot
) -> tuple[SnapshotChange, ...]:
    prev_map = {_rel_key(r): r for r in prev.relations}
    curr_map = {_rel_key(r): r for r in curr.relations}
    return _diff_entity_set(
        prev_map, curr_map, EntityKind.RELATION,
        field_names=("type", "first_ch", "last_ch", "strength"),
    )


def _diff_mood(
    prev: WorldSnapshot, curr: WorldSnapshot
) -> tuple[SnapshotChange, ...]:
    if prev.world_mood == curr.world_mood:
        return ()
    return (
        SnapshotChange(
            kind=ChangeKind.MODIFIED,
            entity=EntityKind.MOOD,
            entity_id="world_mood",
            before=prev.world_mood,
            after=curr.world_mood,
            field_changes=(("value", prev.world_mood, curr.world_mood),),
        ),
    )


def _diff_physical(
    prev: WorldSnapshot, curr: WorldSnapshot
) -> tuple[SnapshotChange, ...]:
    field_changes = _diff_fields(
        prev.physical, curr.physical,
        fields=("ch", "state", "intensity", "notes"),
    )
    if not field_changes:
        return ()
    return (
        SnapshotChange(
            kind=ChangeKind.MODIFIED,
            entity=EntityKind.PHYSICAL,
            entity_id="physical_line",
            before=prev.physical,
            after=curr.physical,
            field_changes=field_changes,
        ),
    )


def _diff_mental(
    prev: WorldSnapshot, curr: WorldSnapshot
) -> tuple[SnapshotChange, ...]:
    field_changes = _diff_fields(
        prev.mental, curr.mental,
        fields=("ch", "state", "intensity", "notes"),
    )
    if not field_changes:
        return ()
    return (
        SnapshotChange(
            kind=ChangeKind.MODIFIED,
            entity=EntityKind.MENTAL,
            entity_id="mental_line",
            before=prev.mental,
            after=curr.mental,
            field_changes=field_changes,
        ),
    )


# ============ 通用 helpers ============

def _diff_entity_set(
    prev_map: dict[str, Any],
    curr_map: dict[str, Any],
    entity: EntityKind,
    field_names: tuple[str, ...] = (),
) -> tuple[SnapshotChange, ...]:
    """通用字典差: ADDED / REMOVED / MODIFIED(by field_names)"""
    changes: list[SnapshotChange] = []

    for k in curr_map:
        if k not in prev_map:
            changes.append(
                SnapshotChange(
                    kind=ChangeKind.ADDED,
                    entity=entity,
                    entity_id=k,
                    after=curr_map[k],
                )
            )
    for k in prev_map:
        if k not in curr_map:
            changes.append(
                SnapshotChange(
                    kind=ChangeKind.REMOVED,
                    entity=entity,
                    entity_id=k,
                    before=prev_map[k],
                )
            )
    for k in prev_map.keys() & curr_map.keys():
        prev_obj = prev_map[k]
        curr_obj = curr_map[k]
        field_changes = _diff_fields(prev_obj, curr_obj, fields=field_names)
        if field_changes:
            changes.append(
                SnapshotChange(
                    kind=ChangeKind.MODIFIED,
                    entity=entity,
                    entity_id=k,
                    before=prev_obj,
                    after=curr_obj,
                    field_changes=field_changes,
                )
            )
    return tuple(changes)


def _diff_fields(
    prev: Any, curr: Any, fields: tuple[str, ...]
) -> tuple[tuple[str, Any, Any], ...]:
    """比较两个 dataclass 在指定 fields 上的差异 → (field, before, after)"""
    changes: list[tuple[str, Any, Any]] = []
    for field in fields:
        prev_val = getattr(prev, field, None)
        curr_val = getattr(curr, field, None)
        if prev_val != curr_val:
            changes.append((field, prev_val, curr_val))
    return tuple(changes)


def _plot_key(plot: Any) -> str:
    """Plot 主键: plot_id (或 str(plot) 兜底, 应对 stub)"""
    return getattr(plot, "plot_id", None) or str(plot)


def _rel_key(rel: Any) -> str:
    """Relation 主键: "src→dst" 字符串"""
    src = getattr(rel, "src", None) or "?"
    dst = getattr(rel, "dst", None) or "?"
    return f"{src}→{dst}"


__all__ = [
    "ChangeKind",
    "EntityKind",
    "SnapshotChange",
    "diff_snapshots",
    "diff_ripples",
    "diff_subplots",
    "has_state_transition",
]
