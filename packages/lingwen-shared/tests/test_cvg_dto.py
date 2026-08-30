"""Contract regression tests for v16.5 #N.7 lingwen-shared cvg contracts.

12 Pydantic models (presentation shape — see cvg.py docstring).
"""
from __future__ import annotations


def test_cvg_dtos_importable() -> None:
    """All CVG DTOs must import from lingwen_shared.contracts.python.cvg."""
    from lingwen_shared.contracts.python.cvg import (  # noqa: F401
        RippleListItemResponse,
        RippleDetailResponse,
        RippleActionResponse,
        RippleStatsResponse,
        RippleAuditEntryResponse,
        CascadeNodeResponse,
        CascadeEdgeResponse,
        CascadeResponse,
        CascadePreviewResponse,
        ReferenceGraphResponse,
        CascadeRunResponse,
        CascadeCancelPayload,
    )


def test_ripple_list_item_basic() -> None:
    """RippleListItemResponse required fields + defaults."""
    from lingwen_shared.contracts.python.cvg import RippleListItemResponse
    obj = RippleListItemResponse(
        ripple_id="r1", chapter_id=10, title="T", status="pending",
        source_volume=1, created_at="2026-08-30T00:00:00Z",
    )
    assert obj.impact_volumes == []
    assert obj.applies_count is None


def test_ripple_detail_inherits_list_item() -> None:
    """RippleDetailResponse extends RippleListItemResponse (all base fields present)."""
    from lingwen_shared.contracts.python.cvg import RippleDetailResponse
    obj = RippleDetailResponse(
        ripple_id="r1", chapter_id=10, title="T", status="pending",
        source_volume=1, created_at="2026-08-30T00:00:00Z",
    )
    assert obj.evidence is None
    assert obj.audit_trail is None


def test_cascade_response_contains_nodes_edges() -> None:
    """CascadeResponse has nodes/edges counts + max_depth."""
    from lingwen_shared.contracts.python.cvg import (
        CascadeResponse, CascadeNodeResponse, CascadeEdgeResponse,
    )
    obj = CascadeResponse(
        ripple_id="r1",
        nodes=[CascadeNodeResponse(node_id="n1", chapter_id=1, title="T", status="x", depth=0)],
        edges=[CascadeEdgeResponse(source="n1", target="n2", relation="causes")],
        total_nodes=1, total_edges=1, max_depth=2,
    )
    assert obj.max_depth == 2


def test_reference_graph_uses_generic_nodes() -> None:
    """ReferenceGraphResponse nodes/edges are list[dict]."""
    from lingwen_shared.contracts.python.cvg import ReferenceGraphResponse
    obj = ReferenceGraphResponse(
        nodes=[{"id": "n1"}], edges=[{"source": "n1", "target": "n2"}],
        total_nodes=1, total_edges=1,
    )
    assert obj.total_nodes == 1
