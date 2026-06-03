"""Tests for world_model.snapshot_store.

Phase 1.1.e — RED tests for SnapshotStore JSON persistence.

MVP scope (1.1):
- save(snapshot) writes to .state/snapshots/ch{NNNN}.json
- load(chapter) returns the saved snapshot, or None if missing
- list_chapters() returns sorted chapter numbers
- integrity check: consistency_hash must match recomputed hash
- new save overwrites previous (no version suffix in MVP; reserved for v2)

Out of scope (later phases):
- Multi-version history (ch0001_v1, _v2, ...)
- SQLite backend
- Compression / incremental storage
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from infra.world_model.data_structures import (
    KeyPoint,
    NodeId,
    NodeType,
    PhysicalLine,
    WorldSnapshot,
)
from infra.world_model.snapshot_store import (
    SnapshotIntegrityError,
    SnapshotNotFoundError,
    SnapshotStore,
)


def _build_snapshot(ch: int) -> WorldSnapshot:
    return WorldSnapshot(
        snapshot_id=f"ch{ch:04d}_v1",
        chapter=ch,
        timestamp=datetime(2026, 5, 21, 10, 0, 0),
        nodes={
            NodeId(NodeType.CHARACTER, "林尘"): KeyPoint(
                id=NodeId(NodeType.CHARACTER, "林尘"),
                attrs={"age": 18 + ch},
            ),
        },
        physical=PhysicalLine(ch=ch, actions=[f"第{ch}章事件"]),
    )


class TestSnapshotStoreBasic:
    def test_save_and_load_roundtrip(self, tmp_path: Path):
        store = SnapshotStore(tmp_path)
        snap = _build_snapshot(1)
        store.save(snap)
        loaded = store.load(1)
        assert loaded == snap

    def test_load_missing_chapter_raises_not_found(self, tmp_path: Path):
        store = SnapshotStore(tmp_path)
        with pytest.raises(SnapshotNotFoundError):
            store.load(99)

    def test_list_chapters_empty(self, tmp_path: Path):
        store = SnapshotStore(tmp_path)
        assert store.list_chapters() == []

    def test_list_chapters_sorted(self, tmp_path: Path):
        store = SnapshotStore(tmp_path)
        store.save(_build_snapshot(3))
        store.save(_build_snapshot(1))
        store.save(_build_snapshot(2))
        assert store.list_chapters() == [1, 2, 3]

    def test_overwrite_existing_snapshot(self, tmp_path: Path):
        store = SnapshotStore(tmp_path)
        store.save(_build_snapshot(1))
        # 改 attrs 再存
        snap2 = WorldSnapshot(
            snapshot_id="ch0001_v2",
            chapter=1,
            timestamp=datetime(2026, 5, 22, 10, 0, 0),
            nodes={
                NodeId(NodeType.CHARACTER, "林尘"): KeyPoint(
                    id=NodeId(NodeType.CHARACTER, "林尘"),
                    attrs={"age": 20},
                ),
            },
        )
        store.save(snap2)
        loaded = store.load(1)
        assert loaded == snap2


class TestSnapshotStoreIntegrity:
    def test_integrity_check_passes_for_valid_snapshot(self, tmp_path: Path):
        store = SnapshotStore(tmp_path)
        snap = _build_snapshot(1)
        store.save(snap)
        # 默认 verify=True,load 不抛
        store.load(1, verify_integrity=True)

    def test_tampered_file_raises_integrity_error(self, tmp_path: Path):
        store = SnapshotStore(tmp_path)
        snap = _build_snapshot(1)
        store.save(snap)

        # 篡改文件 (把 content 改了)
        snap_file = tmp_path / "ch0001.json"
        import json
        data = json.loads(snap_file.read_text(encoding="utf-8"))
        data["world_mood"] = "tampered!"
        snap_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        with pytest.raises(SnapshotIntegrityError):
            store.load(1, verify_integrity=True)

    def test_load_skip_integrity(self, tmp_path: Path):
        store = SnapshotStore(tmp_path)
        snap = _build_snapshot(1)
        store.save(snap)

        # 篡改
        snap_file = tmp_path / "ch0001.json"
        import json
        data = json.loads(snap_file.read_text(encoding="utf-8"))
        data["world_mood"] = "tampered"
        snap_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        # verify=False 时不抛
        loaded = store.load(1, verify_integrity=False)
        assert loaded.world_mood == "tampered"


class TestSnapshotStoreFileFormat:
    def test_filename_format(self, tmp_path: Path):
        store = SnapshotStore(tmp_path)
        store.save(_build_snapshot(7))
        # 文件名是 ch0007.json
        assert (tmp_path / "ch0007.json").exists()

    def test_save_creates_dir_if_missing(self, tmp_path: Path):
        nested = tmp_path / "deep" / "snapshots"
        store = SnapshotStore(nested)
        store.save(_build_snapshot(1))
        assert nested.exists()
        assert (nested / "ch0001.json").exists()
