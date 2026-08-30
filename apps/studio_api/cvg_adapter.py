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

from typing import Any

from lingwen_shared.contracts.python.cvg import (
    CascadeEdgeResponse,
    CascadeNodeResponse,
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
]


def _compute_volume_from_chapter(chapter: int) -> int:
    """Default heuristic: chapter // 100 + 1, clamped to >= 1.

    Replace with project-config-driven volume resolution once
    v16.5 #N.9 wires the adapter into routes.
    """
    if chapter <= 0:
        return 1
    return max(1, (chapter - 1) // 100 + 1)


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
        created_at=storage.get("created_at") or "",
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
    """Map storage cascade node → presentation shape."""
    return CascadeNodeResponse(
        node_id=storage.get("node_id") or storage.get("id", ""),
        chapter_id=storage.get("chapter_id", 0),
        title=storage.get("title") or storage.get("label", ""),
        status=storage.get("status", "applied"),
        depth=storage.get("depth", 0),
        ripple_id=storage.get("ripple_id"),
        volume=storage.get("volume", 1),
    )


def cascade_edge_storage_to_presentation(storage: dict[str, Any]) -> CascadeEdgeResponse:
    """Map storage cascade edge → presentation shape."""
    return CascadeEdgeResponse(
        source=storage.get("source", ""),
        target=storage.get("target", ""),
        relation=storage.get("relation") or storage.get("relationship") or "reference",
        weight=storage.get("weight", 0.0),
    )


def cascade_storage_to_presentation(storage: dict[str, Any]) -> CascadeResponse:
    """Map storage cascade envelope → presentation shape."""
    nodes_raw = storage.get("nodes", [])
    edges_raw = storage.get("edges", [])
    nodes = [cascade_node_storage_to_presentation(n) for n in nodes_raw]
    edges = [cascade_edge_storage_to_presentation(e) for e in edges_raw]
    return CascadeResponse(
        ripple_id=storage.get("ripple_id") or storage.get("cascade_id") or storage.get("id", ""),
        nodes=nodes,
        edges=edges,
        total_nodes=len(nodes),
        total_edges=len(edges),
        max_depth=max((n.depth for n in nodes), default=0),
        status=storage.get("status"),
    )
