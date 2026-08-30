"""Tests for the CVG storage → presentation adapter (apps/studio_api/cvg_adapter.py).

Phase 126 v16.5 #N.8 — boundary marker. Verifies that:
1. Adapter import path works (lingwen-shared reachable from apps/studio_api).
2. Storage → presentation shape conversion produces valid Pydantic instances.
3. Field mapping heuristics compile without error.

Carryover to v16.5 #N.9: integration tests against actual route outputs.
"""
from __future__ import annotations

from apps.studio_api.cvg_adapter import (
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
