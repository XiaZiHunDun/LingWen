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

from datetime import datetime
from typing import Any

from lingwen_shared.contracts.python.cvg import (
    CascadeEdgeResponse,
    CascadeNodeResponse,
    CascadePreviewResponse,
    CascadeResponse,
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
        1 for n in nodes_raw if (n.get("dimension") if isinstance(n, dict) else getattr(n, "dimension", None)) in ("plot_point", "foreshadow")
    )
    affected_characters = sum(
        1 for n in nodes_raw if (n.get("dimension") if isinstance(n, dict) else getattr(n, "dimension", None)) == "character"
    )
    affected_settings = sum(
        1 for n in nodes_raw if (n.get("dimension") if isinstance(n, dict) else getattr(n, "dimension", None)) == "setting"
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
