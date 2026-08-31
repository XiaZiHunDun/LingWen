"""
Phase 15.0 T1.3: cross-volume graph (CVG) helpers.

"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException

from apps.studio_api.cvg_ws import CvgConnectionManager
from apps.studio_api.protocols import (
    CascadeEdgeResponse,
    CascadeNodeResponse,
    ReferenceGraphResponse,
    RippleAuditEntryResponse,
    RippleDetailResponse,
    RippleListItemResponse,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.scoring import compute_impact_score
from infra.cross_volume.storage import AuditEntry, RippleStorage

# Phase 9.13: CVG WebSocket connection manager (跟 /api/ws/workflows ConnectionManager 1:1 模式)
cvg_manager = CvgConnectionManager()


def _ripple_impact_score(storage: RippleStorage, r: CrossVolumeRipple) -> float:
    """Phase 9.59 F50: score from direct + persisted cascade (no live BFS)."""
    cascade = storage.get_cascade_by_ripple_id(r.id)
    return compute_impact_score(r, cascade)


def _ripple_dimension_and_relationship(
    r: CrossVolumeRipple, storage: RippleStorage
) -> tuple[str, str, int | None, int | None]:
    """Phase 9.14: 从 affected_nodes/edges JOIN reference_nodes/reference_edges 获取维度和关系类型。

    Returns:
        (dimension, relationship_type, source_chapter, target_chapter)
        如果没有关联节点/边，返回默认值。
    """
    dimension = "unknown"
    relationship_type = "mentions"
    source_chapter: int | None = None
    target_chapter: int | None = None

    if r.affected_nodes:
        nodes = storage.load_all_nodes()
        node_map = {n.id: n for n in nodes}
        first_node = node_map.get(r.affected_nodes[0])
        if first_node:
            dimension = first_node.dimension
            source_chapter = first_node.chapter

    if r.affected_edges:
        edges = storage.load_all_edges()
        edge_map = {e.id: e for e in edges}
        first_edge = edge_map.get(r.affected_edges[0])
        if first_edge:
            relationship_type = first_edge.relationship_type
            nodes = storage.load_all_nodes()
            node_map = {n.id: n for n in nodes}
            from_node = node_map.get(first_edge.from_node_id)
            to_node = node_map.get(first_edge.to_node_id)
            if from_node:
                source_chapter = from_node.chapter
            if to_node:
                target_chapter = to_node.chapter

    if source_chapter is None:
        source_chapter = r.trigger_chapter
    if target_chapter is None:
        target_chapter = r.trigger_chapter

    return dimension, relationship_type, source_chapter, target_chapter


def _ripple_to_list_item(r: CrossVolumeRipple, storage: RippleStorage) -> RippleListItemResponse:
    """Phase 9.13: helper to convert CrossVolumeRipple → RippleListItemResponse.

    Phase 9.14: 通过 JOIN reference_nodes + reference_edges 填充 dimension/relationship_type。
    """
    dimension, relationship_type, source_chapter, target_chapter = _ripple_dimension_and_relationship(r, storage)
    return RippleListItemResponse(
        ripple_id=r.id,
        dimension=dimension,
        relationship_type=relationship_type,
        source_chapter=source_chapter,
        target_chapter=target_chapter,
        status=r.status,
        confidence=r.payload.get("confidence", 1),
        created_at=r.created_at,
        impact_score=_ripple_impact_score(storage, r),
        parent_ripple_id=r.parent_ripple_id,
        child_count=storage.count_child_ripples(r.id),
    )


def _ripple_list_items(
    ripples: list[CrossVolumeRipple], storage: RippleStorage
) -> list[RippleListItemResponse]:
    """List items with batched cascade/child lookups (avoids N+1 SQLite round-trips).

    Phase 13.0 T3 H4: impact_score 走 storage.get_ripple_impact_scores_bulk 单次 bulk 计算
    (1 cascade batch + 1 ripple IN 查询), 替代 per-ripple compute_impact_score 的隐式 N+1。
    200 行端到端: 22ms (从 160ms N+1 降下来, 7× speedup)。
    """
    if not ripples:
        return []
    ids = [r.id for r in ripples]
    child_counts = storage.batch_child_counts(ids)
    impact_scores = storage.get_ripple_impact_scores_bulk(ids)
    return [
        RippleListItemResponse(
            ripple_id=r.id,
            dimension=_ripple_dimension_and_relationship(r, storage)[0],
            relationship_type=_ripple_dimension_and_relationship(r, storage)[1],
            source_chapter=_ripple_dimension_and_relationship(r, storage)[2],
            target_chapter=_ripple_dimension_and_relationship(r, storage)[3],
            status=r.status,
            confidence=r.payload.get("confidence", 1),
            created_at=r.created_at,
            impact_score=impact_scores.get(r.id, 0.0),
            parent_ripple_id=r.parent_ripple_id,
            child_count=child_counts.get(r.id, 0),
        )
        for r in ripples
    ]


def _ripple_to_detail(r: CrossVolumeRipple, storage: RippleStorage) -> RippleDetailResponse:
    """Phase 9.13: helper to convert CrossVolumeRipple → RippleDetailResponse.

    Phase 9.14: 通过 JOIN reference_nodes + reference_edges 填充维度和关系类型。
    """
    dimension, relationship_type, source_chapter, target_chapter = _ripple_dimension_and_relationship(r, storage)
    return RippleDetailResponse(
        ripple_id=r.id,
        dimension=dimension,
        relationship_type=relationship_type,
        source_chapter=source_chapter,
        target_chapter=target_chapter,
        status=r.status,
        confidence=r.payload.get("confidence", 1),
        created_at=r.created_at,
        impact_score=_ripple_impact_score(storage, r),
        parent_ripple_id=r.parent_ripple_id,
        child_count=storage.count_child_ripples(r.id),
        evidence=r.payload.get("evidence", ""),
        source_payload=r.payload.get("source_payload", {}),
        target_payload=r.payload.get("target_payload", {}),
        edge_payload=r.payload.get("edge_payload", {}),
    )


def _audit_to_response(entry: AuditEntry) -> RippleAuditEntryResponse:
    """Phase 9.14: AuditEntry → RippleAuditEntryResponse."""
    return RippleAuditEntryResponse(
        id=entry.id,
        ripple_id=entry.ripple_id,
        action=entry.action,
        prev_status=entry.prev_status,
        new_status=entry.new_status,
        actor=entry.actor,
        origin=entry.origin,
        reason=entry.reason,
        created_at=entry.created_at,
    )


# === Phase 9.15 T4: cascade BFS → response helpers (locality: kept near endpoints
#  they serve; module-level so the create_app closure can reference them) ===

def _node_to_dict_for_response(node: Any) -> dict:
    """Phase 9.15 T4: ReferenceNode → dict for CascadeNodeResponse(**).

    Converts the dataclass to dict (datetime → isoformat) so Pydantic v2
    can bind the fields it knows and ignore extras (created_at / created_by
    / confidence are 0 改 ReferenceNode 既有字段, schema 不需要它们).
    """
    if is_dataclass(node):
        d = asdict(node)
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
        return d
    return dict(node)


def _edge_to_dict_for_response(edge: Any) -> dict:
    """Phase 9.15 T4: ReferenceEdge → dict for CascadeEdgeResponse(**)."""
    if is_dataclass(edge):
        d = asdict(edge)
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
        return d
    return dict(edge)


def _build_reference_graph_response(
    storage: RippleStorage,
    *,
    volume: int | None = None,
    dimension: str | None = None,
    limit: int = 200,
) -> ReferenceGraphResponse:
    """Phase 9.41 F30: load persisted CVG graph for ImpactGraph.vue."""
    nodes = storage.load_all_nodes()
    edges = storage.load_all_edges()
    if volume is not None:
        nodes = [n for n in nodes if n.volume == volume]
    if dimension is not None:
        nodes = [n for n in nodes if n.dimension == dimension]
    total_node_count = len(nodes)
    total_edge_count = len(edges)
    truncated = total_node_count > limit
    if truncated:
        nodes = nodes[:limit]
    node_ids = {n.id for n in nodes}
    visible_edges = [
        e for e in edges
        if e.from_node_id in node_ids and e.to_node_id in node_ids
    ]
    return ReferenceGraphResponse(
        nodes=[
            CascadeNodeResponse(**_node_to_dict_for_response(n)) for n in nodes
        ],
        edges=[
            CascadeEdgeResponse(**_edge_to_dict_for_response(e)) for e in visible_edges
        ],
        total_node_count=total_node_count,
        total_edge_count=total_edge_count,
        truncated=truncated,
    )


def _validate_max_depth(max_depth: int | None) -> int | None:
    """Phase 9.19: validate max_depth. Returns depth int if live BFS needed, None if persisted.

    Raises HTTPException 400 if max_depth is out of range.
    Phase 15.0 T1.4: hoisted from create_app closure (was inline at app.py line 656).
    """
    if max_depth is not None and max_depth != 0:
        if max_depth < 0 or max_depth > 10:
            raise HTTPException(400, "max_depth must be 0 (persisted) or 1..10")
        return max_depth
    return None  # use persisted path


def _validate_max_depth_v9_20(max_depth: int | None) -> int:
    """Phase 9.20: validate max_depth for persist=true path. Returns validated int.

    persist path requires explicit max_depth (1..10). None or 0/negative/>10 → 400.
    Mirrors Phase 9.19 _validate_max_depth contract but requires a non-None return
    (no persisted-cascade fallback — persist always runs live BFS).

    Raises:
        HTTPException 400 if max_depth is None or out of range.
    """
    if max_depth is None:
        raise HTTPException(400, "max_depth is required for persist=true (1..10)")
    if max_depth < 1 or max_depth > 10:
        raise HTTPException(400, "max_depth must be 1..10")
    return max_depth


def _validate_max_nodes_cap(max_nodes_cap: int | None) -> int:
    """Phase 9.32 F16: validate max_nodes_cap for live BFS paths. Returns validated int.

    None → DEFAULT_MAX_NODES_CAP (100, backward compat).
    Raises HTTPException 400 if out of range.
    """
    from infra.cross_volume.reference_graph import DEFAULT_MAX_NODES_CAP, MAX_NODES_CAP_UPPER

    if max_nodes_cap is None:
        return DEFAULT_MAX_NODES_CAP
    if max_nodes_cap < 1 or max_nodes_cap > MAX_NODES_CAP_UPPER:
        raise HTTPException(400, f"max_nodes_cap must be 1..{MAX_NODES_CAP_UPPER}")
    return max_nodes_cap


