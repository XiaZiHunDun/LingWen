"""Contract regression tests for v16.5 #N.7 lingwen-shared cvg contracts.

12 Pydantic models (presentation shape — see cvg.py docstring).
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError


def test_cvg_dtos_importable() -> None:
    """All CVG DTOs must import from lingwen_shared.contracts.python.cvg."""
    from lingwen_shared.contracts.python.cvg import (  # noqa: F401
        CascadeCancelPayload,
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
        CascadeEdgeResponse,
        CascadeNodeResponse,
        CascadeResponse,
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


def test_cascade_response_includes_cascade_actions_field() -> None:
    """CascadeResponse must include cascade_actions list (dashboard consumer cascadeGraphUtils.js:152)."""
    from lingwen_shared.contracts.python.cvg import CascadeEdgeResponse, CascadeNodeResponse, CascadeResponse
    response = CascadeResponse(
        ripple_id="r1",
        nodes=[CascadeNodeResponse(node_id="n1", chapter_id=1, title="T", status="applied", depth=1)],
        edges=[CascadeEdgeResponse(source="a", target="b", relation="ref")],
        total_nodes=1,
        total_edges=1,
        max_depth=1,
        cascade_actions=[{"type": "apply", "target": "ch1"}],
    )
    assert len(response.cascade_actions) == 1
    assert response.cascade_actions[0]["type"] == "apply"


def test_cascade_response_includes_generated_at_field() -> None:
    """CascadeResponse must include generated_at string (dashboard consumer uses for display)."""
    from lingwen_shared.contracts.python.cvg import CascadeResponse
    response = CascadeResponse(
        ripple_id="r1",
        nodes=[],
        edges=[],
        total_nodes=0,
        total_edges=0,
        max_depth=0,
        cascade_actions=[],
        generated_at="2026-08-30T12:00:00",
    )
    assert response.generated_at == "2026-08-30T12:00:00"


def test_cascade_response_includes_bfs_algorithm_version_field() -> None:
    """CascadeResponse must include bfs_algorithm_version (Literal v1|v2_weighted)."""
    from lingwen_shared.contracts.python.cvg import CascadeResponse
    response_v1 = CascadeResponse(
        ripple_id="r1", nodes=[], edges=[], total_nodes=0, total_edges=0, max_depth=0,
        cascade_actions=[], generated_at="", bfs_algorithm_version="v1",
    )
    assert response_v1.bfs_algorithm_version == "v1"
    with pytest.raises(ValidationError):
        CascadeResponse(
            ripple_id="r1", nodes=[], edges=[], total_nodes=0, total_edges=0, max_depth=0,
            cascade_actions=[], generated_at="", bfs_algorithm_version="v9_invalid",
        )


def test_cascade_preview_response_includes_storage_counts() -> None:
    """CascadePreviewResponse must include storage-shape aggregate counts."""
    from lingwen_shared.contracts.python.cvg import CascadePreviewResponse
    response = CascadePreviewResponse(
        ripple_id="r1",
        estimated_impact=10,
        affected_chapters=[],
        affected_chapter_count=3,
        affected_character_count=5,
        affected_setting_count=2,
        estimated_change_count=10,
        cascade_node_count=8,
        cascade_edge_count=7,
        max_depth=4,
    )
    assert response.affected_chapter_count == 3
    assert response.affected_character_count == 5
    assert response.affected_setting_count == 2
    assert response.estimated_change_count == 10
    assert response.cascade_node_count == 8
    assert response.cascade_edge_count == 7
    assert response.max_depth == 4


def test_cascade_preview_response_storage_counts_default_zero() -> None:
    """CascadePreviewResponse storage-shape counts must default to 0 (not None)."""
    from lingwen_shared.contracts.python.cvg import CascadePreviewResponse
    response = CascadePreviewResponse(ripple_id="r1", estimated_impact=0)
    assert response.affected_chapter_count == 0
    assert response.affected_character_count == 0
    assert response.affected_setting_count == 0
    assert response.estimated_change_count == 0
    assert response.cascade_node_count == 0
    assert response.cascade_edge_count == 0
    assert response.max_depth == 0


def test_cascade_run_response_extended_fields() -> None:
    """Phase 126 v16.5 #N.11.b: CascadeRunResponse extended with 10 storage-shape fields.

    Verifies safe defaults for backward compat with N.9-era minimal instances.
    """
    from lingwen_shared.contracts.python.cvg import CascadeRunResponse

    # Minimal canonical (N.7 presentation shape)
    minimal = CascadeRunResponse(
        run_id="42",
        ripple_id="ripple-abc",
        status="completed",
        started_at="2026-08-30T10:00:00",
        max_depth=5,
        nodes_processed=0,
    )
    assert minimal.cascade_id is None
    assert minimal.completed_at is None
    assert minimal.finished_at is None
    assert minimal.depth_reached == 0
    assert minimal.cascade_nodes == []
    assert minimal.cascade_edges == []
    assert minimal.cascade_actions == []
    assert minimal.cancelled_at is None
    assert minimal.triggered_by is None
    assert minimal.stats is None

    # Full storage-shape extended (N.11.b)
    full = CascadeRunResponse(
        run_id="42",
        cascade_id=42,
        ripple_id="ripple-abc",
        max_depth=5,
        depth_reached=3,
        algorithm="v2_weighted",
        started_at="2026-08-30T10:00:00",
        finished_at="2026-08-30T10:01:30",
        completed_at="2026-08-30T10:01:30",
        status="completed",
        nodes_processed=10,
        cancelled_at="2026-08-30T10:02:00",
        triggered_by="system",
        stats={"duration_ms": 90000},
    )
    assert full.cascade_id == 42
    assert full.completed_at == "2026-08-30T10:01:30"
    assert full.cancelled_at == "2026-08-30T10:02:00"
