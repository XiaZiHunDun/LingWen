"""Phase 9.62 F53: audit.created WS push tests."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from dashboard.cascade_notifier import notify_audit_created, set_ws_manager
from dashboard.protocols import AuditCreatedPayload


@pytest.fixture(autouse=True)
def reset_ws_manager():
    set_ws_manager(None)
    yield
    set_ws_manager(None)


class TestAuditCreatedNotifier:
    def test_notify_audit_created_broadcasts_envelope(self):
        captured = []

        async def _broadcast(envelope):
            captured.append(envelope)

        set_ws_manager(_broadcast)
        notify_audit_created(
            AuditCreatedPayload(
                id=1,
                ripple_id="rip-1",
                action="applied",
                prev_status="pending",
                new_status="applied",
                actor="user",
                origin="ui",
                reason="ok",
                created_at=datetime.now(timezone.utc),
            )
        )
        assert len(captured) == 1
        assert captured[0]["type"] == "audit.created"
        assert captured[0]["payload"]["ripple_id"] == "rip-1"
        assert captured[0]["payload"]["action"] == "applied"

    def test_notify_skips_invalid_payload(self):
        captured = []
        set_ws_manager(lambda envelope: captured.append(envelope))
        notify_audit_created({"ripple_id": "", "action": "bad"})
        assert captured == []

    @pytest.mark.asyncio
    async def test_notify_awaits_async_broadcast(self):
        mock_ws = AsyncMock()
        set_ws_manager(mock_ws)
        notify_audit_created(
            AuditCreatedPayload(
                id=2,
                ripple_id="rip-2",
                action="created",
                prev_status=None,
                new_status="pending",
                actor="system",
                origin="system",
                reason=None,
                created_at=datetime.now(timezone.utc),
            )
        )
        mock_ws.assert_called_once()
        assert mock_ws.call_args.args[0]["type"] == "audit.created"
