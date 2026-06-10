"""Phase 9.17: Pydantic CascadeUpdatePayload schema validation tests (T1).

Spec: 2026-06-11-phase9.17-pydantic-cascade-payload-design.md (commit 8216ebe).
Plan: 2026-06-11-phase9.17-pydantic-cascade-payload.md.

T1 目标: cascade_notifier 接受 typed CascadeUpdatePayload + dict (双路径).
ValidationError 提前 (negative count / typo bfs_version / empty ripple_id).

互补 9.16 既有 tests/dashboard/test_cascade_notifier.py: 4 tests 验证 async
broadcast 行为, 本文件 4 tests 验证 typed schema validation, 0 重叠.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from dashboard import cascade_notifier
from dashboard.protocols import CascadeUpdatePayload


@pytest.fixture(autouse=True)
def _reset_ws_manager():
    """Each test starts with a clean module-level singleton."""
    cascade_notifier.set_ws_manager(None)
    yield
    cascade_notifier.set_ws_manager(None)


class TestCascadeUpdatePayloadSchema:
    """T1 fix RED test: typed payload 必 validate via Pydantic v2."""

    def test_payload_accepts_valid_typed_instance(self):
        """CascadeUpdatePayload typed instance 走 success path, 1 broadcast."""
        captured: list[dict] = []
        mock_ws = MagicMock(side_effect=lambda e: captured.append(e))
        cascade_notifier.set_ws_manager(mock_ws)

        payload = CascadeUpdatePayload(
            ripple_id="r1",
            cascade_node_count=3,
            cascade_edge_count=2,
            depth_reached=2,
            bfs_algorithm_version="v2_weighted",
        )
        cascade_notifier.notify_cascade_update(payload)
        # broadcast envelope shape 1:1 跟 9.16
        assert len(captured) == 1
        assert captured[0]["type"] == "cascade.update"
        assert captured[0]["payload"]["ripple_id"] == "r1"
        assert captured[0]["payload"]["cascade_node_count"] == 3
        assert captured[0]["payload"]["bfs_algorithm_version"] == "v2_weighted"

    def test_payload_rejects_negative_count_via_dict(self):
        """dict 传 cascade_node_count=-1 → Pydantic ValidationError caught, no broadcast."""
        mock_ws = MagicMock()
        cascade_notifier.set_ws_manager(mock_ws)

        cascade_notifier.notify_cascade_update({
            "ripple_id": "r1",
            "cascade_node_count": -1,
            "cascade_edge_count": 2,
            "depth_reached": 2,
            "bfs_algorithm_version": "v2_weighted",
        })
        # ValidationError caught in notifier, no broadcast
        mock_ws.assert_not_called()

    def test_payload_rejects_unknown_bfs_version_via_dict(self):
        """dict 传 bfs_algorithm_version='v3' → Pydantic ValidationError caught."""
        mock_ws = MagicMock()
        cascade_notifier.set_ws_manager(mock_ws)

        cascade_notifier.notify_cascade_update({
            "ripple_id": "r1",
            "cascade_node_count": 0,
            "cascade_edge_count": 0,
            "depth_reached": 0,
            "bfs_algorithm_version": "v3",
        })
        mock_ws.assert_not_called()

    def test_payload_rejects_empty_ripple_id(self):
        """typed CascadeUpdatePayload(ripple_id='', ...) → ValidationError."""
        mock_ws = MagicMock()
        cascade_notifier.set_ws_manager(mock_ws)

        with pytest.raises(Exception):  # Pydantic ValidationError
            payload = CascadeUpdatePayload(
                ripple_id="",
                cascade_node_count=0,
                cascade_edge_count=0,
                depth_reached=0,
                bfs_algorithm_version="v1",
            )
            cascade_notifier.notify_cascade_update(payload)
        # 即使 payload 构造 raise, set_ws_manager 仍 0 broadcast
        mock_ws.assert_not_called()
