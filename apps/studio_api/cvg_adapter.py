"""CVG (Cross-Volume Graph) storage → presentation adapter.

Phase 126 v16.5 #N.8 — extracted boundary marker from apps/studio_api/helpers/cvg.py.

Architectural intent
--------------------
The ``cvg`` API surface has two distinct shapes:

- **Storage shape** (apps.studio_api.protocols.py: ``RippleListItemResponse``,
  ``RippleDetailResponse``, ``CascadeResponse``, etc.) — used by
  ``apps.studio_api/helpers/cvg.py`` and consumed by ``apps/studio_api/routes/cvg.py``
  for ``response_model=...``. Backend persistence owns this shape.

- **Presentation shape** (``lingwen_shared.contracts.python.cvg``: same names
  with different field definitions like ``chapter_id``, ``source_volume``,
  ``impact_volumes``) — promoted from manual TS DTOs in v16.5 #N.7 as the
  canonical dashboard surface, single source of truth in Pydantic v2.

Backend routes currently serve the **storage shape** via the existing
``_ripple_list_items`` helper (apps.studio_api.helpers.cvg). This is the
``PYDANTIC-DRIFT`` documented at lingwen_shared/contracts/python/cvg.py:18-24.

This module is the **canonical boundary** where storage → presentation mapping
will live. It currently exports minimal helper(s) for shape verification; full
mapping logic is deferred to v16.5 #N.9+ when the route layer can be
synchronized with dashboard consumption.

Boundary contract (intended, not yet enforced)
----------------------------------------------
1. ``lingwen_shared.contracts.python.cvg.*`` is the source of truth for the
   dashboard wire shape.
2. ``apps.studio_api/protocols.py`` storage models stay as backend persistence
   concerns (SQLite row shape).
3. Routes must call ``cvg_adapter.<storage_to_presentation>()`` before
   returning CVG responses; the adapter is the SOLE place where the mapping
   happens (no inline mapping in route handlers).
4. Once wired, the import-linter forbidden contract
   ``no_concrete_storage_shape_in_cvg_routes`` will enforce that routes
   import only the presentation shape from ``cvg_adapter``.

Carryover
---------
v16.5 #N.9+ tasks:
- Wire ``cvg_adapter.ripple_storage_to_presentation`` into
  ``apps.studio_api/routes/cvg.py:list_ripples`` (currently routes
  ``_ripple_list_items`` from helpers/cvg.py).
- Decide domain mapping for ``chapter_id`` (proposed: source_chapter),
  ``source_volume`` (proposed: computed from source_chapter range or volume
  lookup table), ``impact_volumes`` (proposed: target_chapter → volume).
- Apply same pattern to ``_ripple_to_detail``, ``_build_reference_graph_response``,
  ``_build_cascade_response`` helpers.
- Update dashboard typed wrappers if field semantics change (consult
  ``apps/dashboard/src/api/cvg.ts`` consumers).
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Optional

from lingwen_shared.contracts.python.cvg import (
    CascadeBroadcastLogResponse,  # NEW in N.11.c
    CascadeEdgeResponse,
    CascadeNodeResponse,
    CascadePreviewResponse,
    CascadeResponse,
    CascadeRunResponse,  # NEW in N.11.b
    ReferenceGraphResponse,  # NEW in N.11.g
    RippleDetailResponse,
    RippleListItemResponse,
)

__all__ = [
    "ripple_storage_to_presentation",
    "ripple_detail_storage_to_presentation",
    "cascade_node_storage_to_presentation",
    "cascade_edge_storage_to_presentation",
    "cascade_storage_to_presentation",
    "cascade_preview_storage_to_presentation",
    "cascade_run_storage_to_presentation",  # NEW in N.11.b
    "cascade_broadcast_log_storage_to_presentation",  # NEW in N.11.c
    "reference_graph_storage_to_presentation",  # NEW in N.11.g
]


def _compute_volume_from_chapter(chapter: int) -> int:
    """Default heuristic: chapter // 100 + 1, clamped to >= 1.

    Replace with project-config-driven volume resolution once
    v16.5 #N.9 wires the adapter into routes.
    """
    if chapter <= 0:
        return 1
    return max(1, (chapter - 1) // 100 + 1)


def _parse_dt(value: Any) -> str:
    """Storage datetime → ISO string for presentation.

    Phase 126 v16.5 #N.9: Implementation gap from N.8 scaffold — defined
    in architecture docstring but not actually called. v16.5 #N.9 wire-up
    requires this conversion so that storage ``datetime`` objects validate
    against presentation ``str`` fields.
    """
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _get_dim(node: Any) -> Optional[str]:
    """Polymorphic accessor for cascade node ``dimension`` field.

    Phase 126 v16.5 #N.11.f: DRY helper for cascade_preview_storage_to_presentation.
    Replaces 3x repeated ``n.get("dimension") if isinstance(n, dict) else
    getattr(n, "dimension", None)`` inline expressions.

    Used for both dict (from asdict() output) and dataclass (from
    CascadedRipple.cascade_nodes) inputs.
    """
    if isinstance(node, dict):
        return node.get("dimension")
    return getattr(node, "dimension", None)


def ripple_storage_to_presentation(storage: dict[str, Any]) -> RippleListItemResponse:
    """Convert storage shape dict → canonical presentation shape.

    Intended target: replaces ``apps.studio_api.helpers.cvg._ripple_list_items``
    once v16.5 #N.9 wires it. Currently NOT wired (route still calls
    storage-shape helper).

    Field mapping (storage → presentation):
        ripple_id           → ripple_id
        source_chapter      → chapter_id
        target_chapter      → (into impact_volumes via _compute_volume_from_chapter)
        trigger_volume      → source_volume
        status              → status
        created_at          → created_at (datetime → ISO string)
        parent_ripple_id    → (dropped — presentation uses relations separately)
        confidence          → (dropped — presentation uses status fields)

    NOTE: Mapping for ``source_volume``, ``impact_volumes``, and ``title`` is
    domain-decision-deferred. v16.5 #N.9+ must validate with actual dashboard
    consumers before enabling this in routes.
    """
    source_chapter = storage.get("source_chapter", 0)
    target_chapter = storage.get("target_chapter", source_chapter)
    source_volume = storage.get("trigger_volume") or _compute_volume_from_chapter(source_chapter)
    impact_volume = _compute_volume_from_chapter(target_chapter)
    return RippleListItemResponse(
        ripple_id=storage.get("ripple_id") or storage.get("id", ""),
        chapter_id=source_chapter,
        title=storage.get("title") or storage.get("dimension", ""),
        status=storage.get("status", "pending"),
        source_volume=source_volume,
        impact_volumes=[impact_volume],
        created_at=_parse_dt(storage.get("created_at")),
        # Phase 126 v16.5 #N.11.d: pass impact_score so dashboard filter/sort
        # reads via the typed wrapper directly. Eliminates the hybrid
        # storage-roundtrip in apps/studio_api/routes/cvg.py:list_ripples.
        impact_score=storage.get("impact_score"),
    )


def ripple_detail_storage_to_presentation(storage: dict[str, Any]) -> RippleDetailResponse:
    """Convert storage shape dict → canonical presentation shape for detail view.

    Currently unused; provided for v16.5 #N.9+ wiring parity.
    """
    base = ripple_storage_to_presentation(storage).model_dump()
    return RippleDetailResponse(
        **base,
        description=storage.get("description"),
        evidence=storage.get("evidence"),
        references=storage.get("references"),
        apply_metadata=storage.get("apply_metadata"),
        audit_trail=None,
    )


def cascade_node_storage_to_presentation(storage: dict[str, Any]) -> CascadeNodeResponse:
    """Map storage cascade node → presentation shape.

    Phase 126 v16.5 #N.10: extend mapping to include dimension→status and ripple_id.
    Storage CascadeNodeResponse has fields: id, dimension, volume, chapter, title,
    description, payload. Presentation has: node_id, chapter_id, title, status,
    depth, ripple_id, volume.
    """
    # dimension is the closest storage analog to status (character/setting/plot_point/foreshadow)
    # When absent, default to 'applied' (matches dashboard expectation)
    dimension = storage.get("dimension")
    return CascadeNodeResponse(
        node_id=storage.get("node_id") or storage.get("id", ""),
        chapter_id=storage.get("chapter_id") or storage.get("chapter", 0),
        title=storage.get("title") or storage.get("label", ""),
        status=dimension if dimension else "applied",
        depth=storage.get("depth", 0),
        ripple_id=storage.get("ripple_id"),
        volume=storage.get("volume", 1),
    )


def cascade_edge_storage_to_presentation(storage: dict[str, Any]) -> CascadeEdgeResponse:
    """Map storage cascade edge → presentation shape.

    Phase 126 v16.5 #N.10: storage fields from_node_id/to_node_id map to
    presentation source/target. relationship_type maps to relation.
    """
    return CascadeEdgeResponse(
        source=storage.get("source") or storage.get("from_node_id", ""),
        target=storage.get("target") or storage.get("to_node_id", ""),
        relation=(
            storage.get("relation")
            or storage.get("relationship_type")
            or storage.get("relationship")
            or "reference"
        ),
        weight=storage.get("weight", 0.0),
    )


def cascade_storage_to_presentation(storage: dict[str, Any]) -> CascadeResponse:
    """Map storage cascade envelope → presentation shape.

    Phase 126 v16.5 #N.10: extend mapping to populate:
    - ripple_id (from trigger_ripple_id)
    - total_nodes / total_edges (computed from len)
    - max_depth (from depth_reached)
    - status (from optional status field)
    - cascade_actions / generated_at / bfs_algorithm_version (storage passthrough)
    """
    nodes_raw = storage.get("nodes") or storage.get("cascade_nodes", [])
    edges_raw = storage.get("edges") or storage.get("cascade_edges", [])
    nodes = [cascade_node_storage_to_presentation(n) for n in nodes_raw]
    edges = [cascade_edge_storage_to_presentation(e) for e in edges_raw]
    max_depth = storage.get("max_depth") or storage.get("depth_reached") or max(
        (n.depth for n in nodes), default=0
    )
    return CascadeResponse(
        ripple_id=(
            storage.get("ripple_id")
            or storage.get("trigger_ripple_id")
            or storage.get("cascade_id")
            or storage.get("id", "")
        ),
        nodes=nodes,
        edges=edges,
        total_nodes=len(nodes),
        total_edges=len(edges),
        max_depth=max_depth,
        status=storage.get("status"),
        cascade_actions=list(storage.get("cascade_actions") or []),
        generated_at=storage.get("generated_at"),
        bfs_algorithm_version=storage.get("bfs_algorithm_version") or "v1",
    )


def cascade_preview_storage_to_presentation(
    storage: dict[str, Any],
    ripple_id: str,
) -> CascadePreviewResponse:
    """Map storage cascade envelope → CascadePreviewResponse (presentation shape).

    Phase 126 v16.5 #N.10: computes the 7 storage-shape aggregate counts that
    the backend CascadePreviewResponse exposes and populates both presentation
    fields (estimated_impact, affected_chapters) and storage-shape counts
    (affected_chapter_count, etc.) on the returned presentation model.

    Storage CascadePreviewResponse fields (apps/studio_api/protocols.py:834-846):
    - ripple_id
    - affected_chapter_count, affected_character_count, affected_setting_count
    - estimated_change_count, cascade_node_count, cascade_edge_count, max_depth

    Presentation CascadePreviewResponse fields (lingwen-shared):
    - ripple_id, estimated_impact, affected_chapters, preview_tree, warnings
    - + storage-shape count fields (added in T3)
    """
    nodes_raw = storage.get("nodes") or storage.get("cascade_nodes", [])
    edges_raw = storage.get("edges") or storage.get("cascade_edges", [])
    affected_chapters = sum(
        1 for n in nodes_raw if _get_dim(n) in ("plot_point", "foreshadow")
    )
    affected_characters = sum(
        1 for n in nodes_raw if _get_dim(n) == "character"
    )
    affected_settings = sum(
        1 for n in nodes_raw if _get_dim(n) == "setting"
    )
    actions_raw = storage.get("cascade_actions") or []
    return CascadePreviewResponse(
        ripple_id=ripple_id,
        estimated_impact=len(actions_raw),
        affected_chapters=[],  # storage doesn't track actual chapter IDs in preview response
        affected_chapter_count=affected_chapters,
        affected_character_count=affected_characters,
        affected_setting_count=affected_settings,
        estimated_change_count=len(actions_raw),
        cascade_node_count=len(nodes_raw),
        cascade_edge_count=len(edges_raw),
        max_depth=storage.get("depth_reached") or storage.get("max_depth", 0),
    )


def cascade_run_storage_to_presentation(storage: dict[str, Any]) -> CascadeRunResponse:
    """Convert storage CascadeRun dataclass (or dict) → presentation CascadeRunResponse.

    Phase 126 v16.5 #N.11.b: route wire-up for /ripples/cascade/{id}/runs,
    /cascade/runs, /ripples/cascade/{id}/runs/{runId}/cancel.

    Field mapping (storage → presentation):
        id (int)              → run_id (str via str(int)) + cascade_id (int)
        ripple_id             → ripple_id
        max_depth             → max_depth
        depth_reached         → depth_reached
        algorithm             → algorithm
        started_at (datetime) → started_at (ISO string)
        completed_at (datetime) → finished_at + completed_at (both ISO)
        status                → status
        cascade_nodes         → cascade_nodes (via cascade_node_storage_to_presentation)
        cascade_edges         → cascade_edges (via cascade_edge_storage_to_presentation)
        cascade_actions       → cascade_actions (passthrough list)
        nodes_processed       → len(cascade_nodes) (computed)

    NOTE: cancel-endpoint fields (cancelled_at/triggered_by) and stats dict
    are populated by route layer after adapter call (route knows which
    endpoint is calling and can attach endpoint-specific metadata).
    """
    nodes_raw = storage.get("cascade_nodes") or []
    edges_raw = storage.get("cascade_edges") or []
    nodes = [cascade_node_storage_to_presentation(n) for n in nodes_raw]
    edges = [cascade_edge_storage_to_presentation(e) for e in edges_raw]
    started_at = _parse_dt(storage.get("started_at"))
    completed_at_raw = storage.get("completed_at")
    completed_at = _parse_dt(completed_at_raw) if completed_at_raw is not None else None
    return CascadeRunResponse(
        run_id=str(storage.get("id", "")),
        cascade_id=storage.get("id"),
        ripple_id=storage.get("ripple_id", ""),
        max_depth=storage.get("max_depth", 0),
        depth_reached=storage.get("depth_reached", 0),
        algorithm=storage.get("algorithm"),
        started_at=started_at,
        finished_at=completed_at,
        completed_at=completed_at,
        status=storage.get("status", "running"),
        nodes_processed=len(nodes),
        cascade_nodes=nodes,
        cascade_edges=edges,
        cascade_actions=list(storage.get("cascade_actions") or []),
    )


def cascade_broadcast_log_storage_to_presentation(
    storage: Any,
) -> CascadeBroadcastLogResponse:
    """Convert storage CascadeBroadcastLogEntry (dataclass or dict) → presentation CascadeBroadcastLogResponse.

    Phase 126 v16.5 #N.11.c: route wire-up for /ripples/cascade/{id}/broadcast-log.

    Field mapping (storage → presentation):
        id (int)            → id
        ripple_id (str)     → ripple_id
        latency_ms (int)    → latency_ms
        created_at (str/datetime) → created_at (ISO string)

    Field set is identical between storage and presentation shape — only
    source-of-truth migration (storage Pydantic class → lingwen-shared
    canonical). No semantic mapping needed.
    """
    if is_dataclass(storage) and not isinstance(storage, type):
        d = asdict(storage)
    elif hasattr(storage, "model_dump"):
        d = storage.model_dump()
    elif isinstance(storage, dict):
        d = storage
    else:
        d = dict(storage)
    return CascadeBroadcastLogResponse(
        id=d.get("id", 0),
        ripple_id=d.get("ripple_id", ""),
        latency_ms=d.get("latency_ms", 0),
        created_at=_parse_dt(d.get("created_at")),
    )


def reference_graph_storage_to_presentation(
    storage: dict[str, Any],
) -> ReferenceGraphResponse:
    """Convert storage ReferenceGraphResponse → canonical presentation shape.

    Phase 126 v16.5 #N.11.g: route wire-up for GET /api/cvg/reference-graph.

    Storage shape fields (apps/studio_api/protocols.py:851) →
        presentation shape:
            CascadeNodeResponse (storage with id/chapter/dimension/volume/
            title/description/payload) → dict (presentation with node_id/
            chapter_id/...):
                id → node_id
                chapter → chapter_id
                dimension, volume, title, payload → passthrough
            CascadeEdgeResponse (storage with from_node_id/to_node_id/
            relationship_type/weight) → dict (presentation with source/
            target/relation/weight):
                from_node_id → source
                to_node_id → target
                relationship_type → relation
            total_node_count → total_nodes
            total_edge_count → total_edges
            truncated → truncated (passthrough)
            by_dimension → COMPUTED from node.dimension counts

    Idempotence: if storage already carries presentation-shape keys
    (node_id, chapter_id, source, target), the adapter prefers them and
    leaves the storage-shape fallbacks unused.
    """
    nodes_raw = storage.get("nodes", [])
    edges_raw = storage.get("edges", [])

    # by_dimension: computed from node.dimension occurrences
    by_dimension: dict[str, int] = {}
    for n in nodes_raw:
        if isinstance(n, dict):
            dim = n.get("dimension")
        else:
            dim = getattr(n, "dimension", None)
        if dim:
            by_dimension[dim] = by_dimension.get(dim, 0) + 1

    def _node_to_presentation_dict(n: Any) -> dict[str, Any]:
        if isinstance(n, dict):
            return {
                "node_id": n.get("node_id") or n.get("id", ""),
                "chapter_id": n.get("chapter_id") or n.get("chapter", 0),
                "dimension": n.get("dimension"),
                "volume": n.get("volume", 1),
                "title": n.get("title"),
                "description": n.get("description"),
                "payload": n.get("payload"),
            }
        return {
            "node_id": getattr(n, "node_id", "") or getattr(n, "id", ""),
            "chapter_id": getattr(n, "chapter_id", 0) or getattr(n, "chapter", 0),
            "dimension": getattr(n, "dimension", None),
            "volume": getattr(n, "volume", 1),
            "title": getattr(n, "title", None),
            "description": getattr(n, "description", None),
            "payload": getattr(n, "payload", None),
        }

    def _edge_to_presentation_dict(e: Any) -> dict[str, Any]:
        if isinstance(e, dict):
            return {
                "source": e.get("source") or e.get("from_node_id", ""),
                "target": e.get("target") or e.get("to_node_id", ""),
                "relation": (
                    e.get("relation")
                    or e.get("relationship_type")
                    or e.get("relationship")
                    or "reference"
                ),
                "weight": e.get("weight"),
            }
        return {
            "source": getattr(e, "source", "") or getattr(e, "from_node_id", ""),
            "target": getattr(e, "target", "") or getattr(e, "to_node_id", ""),
            "relation": (
                getattr(e, "relation", None)
                or getattr(e, "relationship_type", None)
                or "reference"
            ),
            "weight": getattr(e, "weight", None),
        }

    return ReferenceGraphResponse(
        nodes=[_node_to_presentation_dict(n) for n in nodes_raw],
        edges=[_edge_to_presentation_dict(e) for e in edges_raw],
        total_nodes=storage.get("total_nodes") or storage.get("total_node_count", 0),
        total_edges=storage.get("total_edges") or storage.get("total_edge_count", 0),
        truncated=bool(storage.get("truncated", False)),
        by_dimension=by_dimension or None,
    )
