"""Phase 9.14: 2 new REST endpoints (audit/rollback) + 2 schemas + 2 既有 endpoint Optional body."""
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_app
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def storage_with_ripple(tmp_path):
    """Storage with 1 applied ripple pre-seeded for audit/rollback tests."""
    db_path = tmp_path / "api_audit.db"
    storage = RippleStorage(db_path=db_path)
    ripple = CrossVolumeRipple(
        id="rip-api-1", trigger_volume=1, trigger_chapter=1,
        affected_nodes=(), affected_edges=(), proposed_actions=(),
        status="applied",
    )
    storage.append_ripple(ripple)
    return storage, "rip-api-1"


@pytest.fixture
def client(storage_with_ripple, monkeypatch):
    storage, _ = storage_with_ripple
    app = create_app()
    # Override _default_storage dependency
    from dashboard import app as app_module
    monkeypatch.setattr(app_module, "_default_storage", lambda: storage)
    return TestClient(app), "rip-api-1"


class TestGetRippleAudit:
    def test_get_audit_happy(self, client):
        """GET /api/cvg/ripples/{id}/audit returns list of entries."""
        c, rid = client
        resp = c.get(f"/api/cvg/ripples/{rid}/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # append_ripple 'created' audit hook from T2
        assert len(data) >= 1
        assert data[0]["action"] == "created"

    def test_get_audit_404_for_missing(self, client):
        c, _ = client
        resp = c.get("/api/cvg/ripples/rip-nonexistent/audit")
        assert resp.status_code == 404

    def test_get_audit_empty_list(self, client):
        c, rid = client
        resp = c.get("/api/cvg/ripples/rip-no-audit/audit")
        assert resp.status_code == 404  # API checks ripple exists first


class TestPostRollback:
    def test_rollback_happy(self, client):
        c, rid = client
        resp = c.post(
            f"/api/cvg/ripples/{rid}/rollback",
            json={"actor": "user", "origin": "ui", "reason": "test rollback"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"

    def test_rollback_404_for_missing(self, client):
        c, _ = client
        resp = c.post(
            "/api/cvg/ripples/rip-nonexistent/rollback",
            json={"actor": "user", "origin": "ui", "reason": "r"},
        )
        assert resp.status_code == 404

    def test_rollback_422_for_pending_status(self, client):
        c, rid = client
        # First rollback → status=pending
        c.post(f"/api/cvg/ripples/{rid}/rollback", json={"actor": "u", "origin": "ui", "reason": "r1"})
        # Second rollback → 422 (not applied/rejected anymore)
        resp = c.post(
            f"/api/cvg/ripples/{rid}/rollback",
            json={"actor": "u", "origin": "ui", "reason": "r2"},
        )
        assert resp.status_code == 422

    def test_rollback_422_for_empty_reason(self, client):
        c, rid = client
        resp = c.post(
            f"/api/cvg/ripples/{rid}/rollback",
            json={"actor": "u", "origin": "ui", "reason": ""},
        )
        assert resp.status_code == 422


class TestBackwardCompat:
    def test_apply_accepts_optional_actor_origin(self, client):
        """POST /apply 不传 body 仍 work (backward compat, Phase 9.13 baseline)."""
        c, rid = client
        # First rollback to pending
        c.post(
            f"/api/cvg/ripples/{rid}/rollback",
            json={"actor": "u", "origin": "ui", "reason": "r"},
        )
        # Now apply without body
        resp = c.post(f"/api/cvg/ripples/{rid}/apply")
        assert resp.status_code == 200
