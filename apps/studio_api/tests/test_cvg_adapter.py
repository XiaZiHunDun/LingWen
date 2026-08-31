"""Tests for the CVG storage → presentation adapter (apps/studio_api/cvg_adapter.py).

Phase 126 v16.5 #N.8 — boundary marker. Verifies that:
1. Adapter import path works (lingwen-shared reachable from apps/studio_api).
2. Storage → presentation shape conversion produces valid Pydantic instances.
3. Field mapping heuristics compile without error.

Carryover to v16.5 #N.9: integration tests against actual route outputs.

Phase 126 v16.5 #N.10: extended mapping coverage — cascade_node/edge/cascade
adapters populate dimension→status, from_node_id/to_node_id→source/target,
trigger_ripple_id→ripple_id, cascade_nodes/cascade_edges keys, and the
extended CascadeResponse fields (cascade_actions / generated_at /
bfs_algorithm_version).
"""
from __future__ import annotations

from apps.studio_api.cvg_adapter import (
    cascade_edge_storage_to_presentation,
    cascade_node_storage_to_presentation,
    cascade_preview_storage_to_presentation,
    cascade_storage_to_presentation,
    ripple_detail_storage_to_presentation,
    ripple_storage_to_presentation,
)


def test_ripple_storage_to_presentation_basic():
    """Storage shape (source_chapter / trigger_volume) → presentation (chapter_id / source_volume / impact_volumes)."""
    storage = {
        "ripple_id": "r-001",
        "source_chapter": 15,
        "target_chapter": 50,
        "trigger_volume": 1,
        "status": "pending",
        "created_at": "2026-08-30T12:00:00",
        "dimension": "character",
    }
    result = ripple_storage_to_presentation(storage)
    assert result.ripple_id == "r-001"
    assert result.chapter_id == 15
    assert result.source_volume == 1
    assert result.impact_volumes == [1]  # target_chapter=50 → vol 1
    assert result.status == "pending"
    assert result.created_at == "2026-08-30T12:00:00"


def test_ripple_storage_to_presentation_uses_compute_volume_fallback():
    """When trigger_volume absent, computes from chapter heuristic."""
    storage = {
        "ripple_id": "r-002",
        "source_chapter": 150,  # → vol 2 by heuristic ((150-1)//100 + 1 = 2)
        "target_chapter": 220,  # → vol 3
        "status": "pending",
    }
    result = ripple_storage_to_presentation(storage)
    assert result.source_volume == 2
    assert result.impact_volumes == [3]


def test_ripple_storage_to_presentation_accepts_datetime():
    """Real storage may pass datetime objects; adapter accepts string-convertible values."""
    storage = {
        "ripple_id": "r-003",
        "source_chapter": 5,
        "target_chapter": 5,
        "trigger_volume": 1,
        "status": "applied",
        "created_at": "2026-08-30T12:00:00",
    }
    result = ripple_storage_to_presentation(storage)
    assert isinstance(result.created_at, str)


def test_ripple_detail_storage_to_presentation_extends_base():
    """Detail shape inherits list shape + adds detail-only fields."""
    storage = {
        "ripple_id": "r-004",
        "source_chapter": 42,
        "status": "pending",
        "description": "cross-volume ref",
        "evidence": {"clause": 1},
    }
    result = ripple_detail_storage_to_presentation(storage)
    assert result.ripple_id == "r-004"
    assert result.chapter_id == 42
    assert result.description == "cross-volume ref"
    assert result.evidence == {"clause": 1}


def test_cascade_storage_to_presentation_composes_nodes_and_edges():
    """Cascade envelope maps each node/edge via the dedicated converters."""
    storage = {
        "cascade_id": "c-001",
        "nodes": [
            {"node_id": "n-1", "label": "Alice", "chapter_id": 10, "depth": 0, "title": "Alice (vol 1)", "status": "applied"},
            {"node_id": "n-2", "label": "Bob", "chapter_id": 50, "depth": 1, "title": "Bob (vol 1)", "status": "applied"},
        ],
        "edges": [
            {"edge_id": "e-1", "source": "n-1", "target": "n-2"},
        ],
    }
    result = cascade_storage_to_presentation(storage)
    assert result.ripple_id == "c-001"
    assert len(result.nodes) == 2
    assert len(result.edges) == 1
    assert result.nodes[0].node_id == "n-1"
    assert result.nodes[0].chapter_id == 10
    assert result.edges[0].source == "n-1"
    assert result.total_nodes == 2
    assert result.total_edges == 1


# ---------------------------------------------------------------------------
# Phase 126 v16.5 #N.10 — extended mapping coverage
# ---------------------------------------------------------------------------


def test_cascade_node_storage_to_presentation_maps_dimension_to_status():
    """Storage node dimension field should populate presentation status (default 'applied')."""
    result_char = cascade_node_storage_to_presentation({
        "id": "n1", "chapter": 1, "title": "T", "dimension": "character",
        "volume": 1, "depth": 1,
    })
    assert result_char.status == "character"  # dimension mapped to status

    result_default = cascade_node_storage_to_presentation({
        "id": "n2", "chapter": 2, "title": "T2", "volume": 1, "depth": 1,
    })
    assert result_default.status == "applied"  # default when no dimension


def test_cascade_edge_storage_to_presentation_maps_from_node_id_and_to_node_id():
    """Storage edge (from_node_id, to_node_id) must map to presentation (source, target)."""
    result = cascade_edge_storage_to_presentation({
        "id": "e1",
        "from_node_id": "n1",
        "to_node_id": "n2",
        "relationship_type": "reference",
        "weight": 0.5,
    })
    assert result.source == "n1"
    assert result.target == "n2"
    assert result.relation == "reference"
    assert result.weight == 0.5


def test_cascade_storage_to_presentation_maps_trigger_ripple_id_and_computes_totals():
    """Storage cascade (trigger_ripple_id + cascade_nodes + cascade_edges) must map correctly."""
    result = cascade_storage_to_presentation({
        "trigger_ripple_id": "r1",
        "cascade_nodes": [
            {"id": "n1", "chapter": 1, "title": "T1", "dimension": "character", "volume": 1, "depth": 1},
            {"id": "n2", "chapter": 2, "title": "T2", "dimension": "setting", "volume": 1, "depth": 2},
        ],
        "cascade_edges": [
            {"id": "e1", "from_node_id": "n1", "to_node_id": "n2", "relationship_type": "ref", "weight": 0.3},
        ],
        "cascade_actions": [{"type": "apply", "target": "ch1"}],
        "depth_reached": 2,
        "generated_at": "2026-08-30T12:00:00",
        "bfs_algorithm_version": "v1",
    })
    assert result.ripple_id == "r1"
    assert len(result.nodes) == 2
    assert result.nodes[0].node_id == "n1"
    assert result.nodes[0].chapter_id == 1
    assert result.total_nodes == 2
    assert len(result.edges) == 1
    assert result.edges[0].source == "n1"
    assert result.edges[0].target == "n2"
    assert result.total_edges == 1
    assert result.max_depth == 2
    assert result.status is None
    assert len(result.cascade_actions) == 1
    assert result.cascade_actions[0]["type"] == "apply"
    assert result.generated_at == "2026-08-30T12:00:00"
    assert result.bfs_algorithm_version == "v1"


def test_cascade_preview_storage_to_presentation_populates_counts():
    """Cascade preview envelope (cascade_nodes/edges/actions/depth_reached) maps to 7 storage-shape aggregate counts plus presentation fields."""
    result = cascade_preview_storage_to_presentation(
        {
            "cascade_nodes": [
                {"id": "n1", "dimension": "character", "chapter": 1, "volume": 1, "title": "C1", "depth": 1},
                {"id": "n2", "dimension": "setting", "chapter": 2, "volume": 1, "title": "S1", "depth": 2},
                {"id": "n3", "dimension": "plot_point", "chapter": 3, "volume": 1, "title": "P1", "depth": 3},
            ],
            "cascade_edges": [
                {"id": "e1", "from_node_id": "n1", "to_node_id": "n2", "relationship_type": "ref", "weight": 0.5},
            ],
            "cascade_actions": [{"type": "apply"}],
            "depth_reached": 3,
        },
        "r1",
    )
    assert result.ripple_id == "r1"
    assert result.affected_chapter_count == 1  # plot_point
    assert result.affected_character_count == 1
    assert result.affected_setting_count == 1
    assert result.estimated_change_count == 1
    assert result.cascade_node_count == 3
    assert result.cascade_edge_count == 1
    assert result.max_depth == 3
    # Presentation fields populated too
    assert result.estimated_impact == 1
    assert result.affected_chapters == []  # storage doesn't carry per-chapter IDs


# ---------------------------------------------------------------------------
# Phase 126 v16.5 #N.11.b — CascadeRunResponse adapter
# ---------------------------------------------------------------------------


def test_cascade_run_storage_to_presentation_basic():
    """Storage CascadeRun → presentation CascadeRunResponse (N.11.b)."""
    from datetime import datetime

    from apps.studio_api.cvg_adapter import cascade_run_storage_to_presentation

    started = datetime(2026, 8, 30, 10, 0, 0)
    completed = datetime(2026, 8, 30, 10, 1, 30)
    storage = {
        "id": 42,
        "ripple_id": "ripple-abc",
        "max_depth": 5,
        "depth_reached": 3,
        "algorithm": "v2_weighted",
        "started_at": started,
        "completed_at": completed,
        "status": "completed",
        "cascade_nodes": [
            {"id": "n1", "dimension": "character", "volume": 1, "chapter": 5, "title": "Lin"},
        ],
        "cascade_edges": [
            {"id": "e1", "from_node_id": "n1", "to_node_id": "n2", "relationship_type": "mentions", "weight": 1.0},
        ],
        "cascade_actions": [{"action": "update", "chapter": 5}],
    }
    result = cascade_run_storage_to_presentation(storage)
    assert result.run_id == "42"
    assert result.ripple_id == "ripple-abc"
    assert result.status == "completed"
    assert result.started_at == started.isoformat()
    assert result.finished_at == completed.isoformat()
    assert result.completed_at == completed.isoformat()
    assert result.cascade_id == 42
    assert result.max_depth == 5
    assert result.depth_reached == 3
    assert result.algorithm == "v2_weighted"
    assert result.nodes_processed == 1
    assert len(result.cascade_nodes) == 1
    assert result.cascade_nodes[0].node_id == "n1"
    assert len(result.cascade_edges) == 1
    assert result.cascade_edges[0].source == "n1"
    assert result.cascade_actions == [{"action": "update", "chapter": 5}]
