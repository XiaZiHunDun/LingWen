"""
Phase 15.0 T1.3: cross-volume graph (CVG) helpers.

Extracted from dashboard/app.py (lines 360-583). Unchanged.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import AuditEntry, RippleStorage
from infra.cross_volume.scoring import compute_impact_score

from dashboard.cvg_ws import CvgConnectionManager
from dashboard.protocols import (
    CascadeEdgeResponse,
    CascadeNodeResponse,
    CascadePreviewResponse,
    CascadeResponse,
    CascadeRunResponse,
    ReferenceGraphResponse,
    RippleActionResponse,
    RippleAuditEntryResponse,
    RippleDetailResponse,
    RippleListItemResponse,
    RippleStatsResponse,
)


# Module-level singleton (跟 _default_decision_queue 1:1 pattern);test fixture override
# via monkeypatch.setattr(app_module, "_default_storage", ...)。

_DEFAULT_CVG_DB_PATH = Path(__file__).parent.parent / ".state" / "cross_volume.db"
_default_storage_instance: RippleStorage | None = None

# Phase 9.13: CVG WebSocket connection manager (跟 /api/ws/workflows ConnectionManager 1:1 模式)
cvg_manager = CvgConnectionManager()


def _default_storage() -> RippleStorage:
    """Phase 9.13: singleton RippleStorage for cvg endpoints.

    Lazy init: first call creates RippleStorage, subsequent calls return cached.
    跟 dashboard 内部 _default_decision_queue 1:1 pattern (但 decisions 是 queue,
    CVG 是 SQLite-backed RippleStorage)。
    """
    global _default_storage_instance
    if _default_storage_instance is None:
        from infra.cross_volume.reference_graph import CrossVolumeReferenceGraph

        storage = RippleStorage(db_path=_DEFAULT_CVG_DB_PATH)
        if storage._graph is None:
            storage._graph = CrossVolumeReferenceGraph(storage)
        _default_storage_instance = storage
    return _default_storage_instance


def _ripple_impact_score(storage: RippleStorage, r: CrossVolumeRipple) -> float:
    """Phase 9.59 F50: score from direct + persisted cascade (no live BFS)."""
    cascade = storage.get_cascade_by_ripple_id(r.id)
    return compute_impact_score(r, cascade)


def _ripple_to_list_item(r: CrossVolumeRipple, storage: RippleStorage) -> RippleListItemResponse:
    """Phase 9.13: helper to convert CrossVolumeRipple → RippleListItemResponse.

    dimension / relationship_type 暂用 placeholder (Phase 9.14 通过 JOIN reference_nodes
    + reference_edges 填充); source_chapter / target_chapter 暂用 trigger_chapter 占位
    (Phase 9.14 真实化 — 从 affected_nodes 第一个 node 的 chapter 提取)。
    """
    return RippleListItemResponse(
        ripple_id=r.id,
        dimension="unknown",  # TODO: Phase 9.14 JOIN reference_nodes
        relationship_type="mentions",  # TODO: Phase 9.14 JOIN reference_edges
        source_chapter=r.trigger_chapter,
        target_chapter=r.trigger_chapter,
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
            dimension="unknown",
            relationship_type="mentions",
            source_chapter=r.trigger_chapter,
            target_chapter=r.trigger_chapter,
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
    """Phase 9.13: helper to convert CrossVolumeRipple → RippleDetailResponse."""
    return RippleDetailResponse(
        ripple_id=r.id,
        dimension="unknown",
        relationship_type="mentions",
        source_chapter=r.trigger_chapter,
        target_chapter=r.trigger_chapter,
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
    from dataclasses import asdict, is_dataclass
    if is_dataclass(node):
        d = asdict(node)
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
        return d
    return dict(node)


def _edge_to_dict_for_response(edge: Any) -> dict:
    """Phase 9.15 T4: ReferenceEdge → dict for CascadeEdgeResponse(**)."""
    from dataclasses import asdict, is_dataclass
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


