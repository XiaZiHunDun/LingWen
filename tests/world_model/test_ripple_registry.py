"""Tests for world_model.registry (Phase 1.5 — RippleRegistry).

CRUD + 10-limit + JSON 持久化 (mirror infra/subplot/registry.py)。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from infra.world_model.data_structures import (
    NodeId,
    NodeType,
    Ripple,
    RippleState,
)
from infra.world_model.lifecycle import MAX_OPEN_RIPPLOTS
from infra.world_model.registry import (
    DuplicateRippleIdError,
    OpenRippleLimitExceeded,
    RippleNotFoundError,
    RippleRegistry,
)


def _ripple(ripple_id: str = "r1", state: RippleState = RippleState.OPEN) -> Ripple:
    return Ripple(
        ripple_id=ripple_id,
        origin_event="e",
        origin_ch=1,
        state=state,
        planned_resolve_ch=10,
    )


# === TestRippleRegistryCRUD ===

class TestRippleRegistryCRUD:
    def test_empty_registry(self, tmp_path: Path):
        reg = RippleRegistry(base_dir=tmp_path)
        assert reg.list_active() == ()
        assert reg.get_ripple("nonexistent") is None

    def test_add_and_get_ripple(self, tmp_path: Path):
        reg = RippleRegistry(base_dir=tmp_path)
        r = _ripple("r1")
        reg.add_ripple(r)
        assert reg.get_ripple("r1") == r

    def test_add_duplicate_raises(self, tmp_path: Path):
        reg = RippleRegistry(base_dir=tmp_path)
        reg.add_ripple(_ripple("r1"))
        with pytest.raises(DuplicateRippleIdError):
            reg.add_ripple(_ripple("r1"))

    def test_remove_ripple(self, tmp_path: Path):
        reg = RippleRegistry(base_dir=tmp_path)
        reg.add_ripple(_ripple("r1"))
        reg.remove_ripple("r1")
        assert reg.get_ripple("r1") is None

    def test_remove_nonexistent_raises(self, tmp_path: Path):
        reg = RippleRegistry(base_dir=tmp_path)
        with pytest.raises(RippleNotFoundError):
            reg.remove_ripple("nonexistent")

    def test_update_ripple_replaces(self, tmp_path: Path):
        reg = RippleRegistry(base_dir=tmp_path)
        reg.add_ripple(_ripple("r1"))
        updated = Ripple(
            ripple_id="r1", origin_event="e", origin_ch=1,
            state=RippleState.PROPAGATING, planned_resolve_ch=10,
        )
        reg.update_ripple(updated)
        assert reg.get_ripple("r1") == updated


# === TestRippleRegistryLimit ===

class TestRippleRegistryLimit:
    def test_add_under_limit_succeeds(self, tmp_path: Path):
        reg = RippleRegistry(base_dir=tmp_path)
        for i in range(MAX_OPEN_RIPPLOTS):
            reg.add_ripple(_ripple(f"r{i}"))
        assert reg.count_open() == MAX_OPEN_RIPPLOTS

    def test_add_over_limit_raises(self, tmp_path: Path):
        reg = RippleRegistry(base_dir=tmp_path)
        for i in range(MAX_OPEN_RIPPLOTS):
            reg.add_ripple(_ripple(f"r{i}"))
        with pytest.raises(OpenRippleLimitExceeded):
            reg.add_ripple(_ripple("r_overflow"))

    def test_resolved_does_not_count_toward_limit(self, tmp_path: Path):
        # RESOLVED 不计入 10-limit,可以无限添加
        reg = RippleRegistry(base_dir=tmp_path)
        for i in range(MAX_OPEN_RIPPLOTS):
            reg.add_ripple(_ripple(f"r{i}", state=RippleState.RESOLVED))
        # 还可加 1 个 OPEN
        reg.add_ripple(_ripple("r_new", state=RippleState.OPEN))
        assert reg.count_open() == 1  # 只算 OPEN+PROPAGATING+RESOLVING

    def test_resolving_counts_toward_limit(self, tmp_path: Path):
        # 用户确认:RESOLVING 计入 10-limit
        reg = RippleRegistry(base_dir=tmp_path)
        for i in range(MAX_OPEN_RIPPLOTS - 1):
            reg.add_ripple(_ripple(f"r{i}"))
        reg.add_ripple(_ripple("r_resolving", state=RippleState.RESOLVING))
        # 满了
        with pytest.raises(OpenRippleLimitExceeded):
            reg.add_ripple(_ripple("r_new", state=RippleState.OPEN))


# === TestRippleRegistryPersistence ===

class TestRippleRegistryPersistence:
    def test_save_and_load_roundtrip(self, tmp_path: Path):
        reg1 = RippleRegistry(base_dir=tmp_path)
        reg1.add_ripple(_ripple("r1"))
        reg1.add_ripple(_ripple("r2", state=RippleState.PROPAGATING))
        reg1.save()

        # 新 registry 从同目录 load
        reg2 = RippleRegistry(base_dir=tmp_path)
        reg2.load()
        assert reg2.get_ripple("r1") is not None
        assert reg2.get_ripple("r2").state == RippleState.PROPAGATING

    def test_save_creates_file(self, tmp_path: Path):
        reg = RippleRegistry(base_dir=tmp_path)
        reg.add_ripple(_ripple("r1"))
        reg.save()
        files = list(tmp_path.iterdir())
        assert any(f.name == "registry.json" for f in files)

    def test_load_missing_file_creates_empty(self, tmp_path: Path):
        reg = RippleRegistry(base_dir=tmp_path)
        reg.load()  # 不存在 → 空 registry
        assert reg.list_active() == ()

    def test_default_base_dir_uses_env_var(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("LINGWEN_RIPPLE_DIR", str(tmp_path))
        reg = RippleRegistry()
        reg.add_ripple(_ripple("r1"))
        reg.save()
        assert (tmp_path / "registry.json").exists()
