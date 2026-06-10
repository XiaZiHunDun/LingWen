"""Phase 9.13: storage 3 new methods (get_ripples / get_ripple_by_id / update_ripple_status) + ConflictError."""
import sys

import pytest

from infra.cross_volume.reference_graph import ReferenceNode
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import ConflictError, RippleStorage


def _make_ripple(status="pending", volume=1, chapter=1):
    return CrossVolumeRipple(
        id=f"rip-{status}-{volume}-{chapter}",
        trigger_volume=volume,
        trigger_chapter=chapter,
        affected_nodes=(),
        affected_edges=(),
        proposed_actions=(),
        status=status,
    )


@pytest.fixture
def storage(tmp_path):
    return RippleStorage(db_path=tmp_path / "test.db")


class TestGetRipples:
    def test_empty_storage_returns_empty_list(self, storage):
        assert storage.get_ripples() == []

    def test_filter_by_status(self, storage):
        for s in ("pending", "applied", "rejected"):
            storage.append_ripple(_make_ripple(status=s))
        result = storage.get_ripples(status="applied")
        assert len(result) == 1
        assert result[0].status == "applied"

    def test_filter_by_volume(self, storage):
        for v in (1, 2, 3):
            storage.append_ripple(_make_ripple(volume=v))
        result = storage.get_ripples(volume=2)
        assert len(result) == 1
        assert result[0].trigger_volume == 2

    def test_filter_combined(self, storage):
        for s in ("pending", "applied"):
            for v in (1, 2):
                storage.append_ripple(_make_ripple(status=s, volume=v))
        result = storage.get_ripples(status="pending", volume=1)
        assert len(result) == 1

    def test_pagination_limit_offset(self, storage):
        for i in range(5):
            storage.append_ripple(_make_ripple(chapter=i))
        page1 = storage.get_ripples(limit=2, offset=0)
        page2 = storage.get_ripples(limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id


class TestGetRippleById:
    def test_existing_ripple_returns_it(self, storage):
        r = _make_ripple()
        storage.append_ripple(r)
        fetched = storage.get_ripple_by_id(r.id)
        assert fetched is not None
        assert fetched.id == r.id

    def test_missing_ripple_returns_none(self, storage):
        assert storage.get_ripple_by_id("nonexistent") is None


class TestUpdateRippleStatus:
    def test_apply_pending_changes_status_and_timestamps(self, storage):
        r = _make_ripple(status="pending")
        storage.append_ripple(r)
        updated = storage.update_ripple_status(r.id, "applied", actor="user")
        assert updated.status == "applied"
        assert updated.applied_at is not None
        assert storage.get_ripple_by_id(r.id).status == "applied"

    def test_reject_pending_changes_status(self, storage):
        r = _make_ripple(status="pending")
        storage.append_ripple(r)
        storage.update_ripple_status(r.id, "rejected", actor="user")
        assert storage.get_ripple_by_id(r.id).status == "rejected"

    def test_invalid_status_raises_value_error(self, storage):
        r = _make_ripple()
        storage.append_ripple(r)
        with pytest.raises(ValueError):
            storage.update_ripple_status(r.id, "weird_status")

    def test_missing_ripple_raises_key_error(self, storage):
        with pytest.raises(KeyError):
            storage.update_ripple_status("nope", "applied")

    def test_already_terminal_raises_conflict_error(self, storage):
        r = _make_ripple(status="applied")
        storage.append_ripple(r)
        with pytest.raises(ConflictError):
            storage.update_ripple_status(r.id, "rejected")

    def test_broadcast_hook_called_on_status_change(self, storage):
        """Phase 9.13: update_ripple_status 末尾 lazy import + broadcast WS event."""
        broadcast_called = []

        class _MockManager:
            def broadcast(self, event):
                broadcast_called.append(event)

        # Mock dashboard.cvg_ws (lazy import target)
        mock_module = type(sys)("dashboard.cvg_ws")
        mock_module.broadcast = _MockManager().broadcast
        sys.modules["dashboard.cvg_ws"] = mock_module

        r = _make_ripple()
        storage.append_ripple(r)
        storage.update_ripple_status(r.id, "applied", actor="user")

        assert len(broadcast_called) == 1
        assert broadcast_called[0]["type"] == "ripple_status_changed"
        assert broadcast_called[0]["data"]["ripple_id"] == r.id
