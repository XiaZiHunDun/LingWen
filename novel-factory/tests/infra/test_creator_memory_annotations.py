"""Tests for creator_memory_annotations."""
from __future__ import annotations

from pathlib import Path

from infra.creator_memory_annotations import (
    apply_memory_annotations,
    load_memory_annotations,
    upsert_memory_annotation,
)


def test_upsert_and_load_annotation(tmp_path: Path) -> None:
    upsert_memory_annotation(tmp_path, "memory-ch-1", note="主角线索", pinned=True)
    data = load_memory_annotations(tmp_path)
    assert data["memory-ch-1"]["note"] == "主角线索"
    assert data["memory-ch-1"]["pinned"] is True


def test_apply_memory_annotations_sorts_pinned_first() -> None:
    items = [
        {"id": "a", "name": "A", "placeholder": False},
        {"id": "b", "name": "B", "placeholder": False},
    ]
    annotations = {"b": {"pinned": True, "note": "重要"}}
    out = apply_memory_annotations(items, annotations)
    assert out[0]["id"] == "b"
    assert out[0]["note"] == "重要"
