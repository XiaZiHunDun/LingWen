"""Phase 9.13: 5 REST endpoints + 4 Pydantic schemas.

Test the FastAPI layer for cross-volume ripple (CVG) review UI.
End-to-end test via TestClient + tmp_path RippleStorage.
"""
import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_app
from dashboard.protocols import (
    RippleActionResponse,
    RippleDetailResponse,
    RippleListItemResponse,
    RippleStatsResponse,
)
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import ConflictError, RippleStorage


@pytest.fixture
def storage(tmp_path):
    return RippleStorage(db_path=tmp_path / "test.db")


@pytest.fixture
def client(storage, monkeypatch):
    """Create FastAPI TestClient with cvg_storage dependency overridden."""
    from dashboard import app as app_module
    monkeypatch.setattr(app_module, "_default_storage", lambda: storage)
    app = create_app()
    return TestClient(app)


def _seed(storage, count=3, status="pending"):
    ids = []
    for i in range(count):
        r = CrossVolumeRipple(
            id=f"rip-{status}-{i}",
            trigger_volume=(i % 3) + 1,
            trigger_chapter=i,
            status=status,
        )
        storage.append_ripple(r)
        ids.append(r.id)
    return ids


class TestListRipples:
    def test_empty_returns_empty_list(self, client):
        resp = client.get("/api/cvg/ripples")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_seeded_returns_list(self, client, storage):
        _seed(storage, count=2)
        resp = client.get("/api/cvg/ripples")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert "ripple_id" in data[0]
        assert "status" in data[0]

    def test_filter_by_status(self, client, storage):
        _seed(storage, count=2, status="pending")
        _seed(storage, count=1, status="applied")
        resp = client.get("/api/cvg/ripples?status=applied")
        assert len(resp.json()) == 1
        assert resp.json()[0]["status"] == "applied"

    def test_filter_invalid_status_returns_422(self, client):
        resp = client.get("/api/cvg/ripples?status=invalid")
        assert resp.status_code == 422

    def test_pagination(self, client, storage):
        _seed(storage, count=5)
        resp1 = client.get("/api/cvg/ripples?limit=2&offset=0")
        resp2 = client.get("/api/cvg/ripples?limit=2&offset=2")
        assert len(resp1.json()) == 2
        assert len(resp2.json()) == 2


class TestGetRippleDetail:
    def test_existing_returns_detail(self, client, storage):
        ids = _seed(storage, count=1)
        resp = client.get(f"/api/cvg/ripples/{ids[0]}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ripple_id"] == ids[0]
        assert "evidence" in data
        assert "source_payload" in data

    def test_missing_returns_404(self, client):
        resp = client.get("/api/cvg/ripples/nonexistent")
        assert resp.status_code == 404


class TestApplyRipple:
    def test_apply_pending_returns_200(self, client, storage):
        ids = _seed(storage, count=1, status="pending")
        resp = client.post(f"/api/cvg/ripples/{ids[0]}/apply")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "applied"
        assert data["actor"] == "user"

    def test_apply_missing_returns_404(self, client):
        resp = client.post("/api/cvg/ripples/nope/apply")
        assert resp.status_code == 404

    def test_apply_terminal_returns_409(self, client, storage):
        ids = _seed(storage, count=1, status="applied")
        resp = client.post(f"/api/cvg/ripples/{ids[0]}/apply")
        assert resp.status_code == 409


class TestRejectRipple:
    def test_reject_pending_returns_200(self, client, storage):
        ids = _seed(storage, count=1, status="pending")
        resp = client.post(f"/api/cvg/ripples/{ids[0]}/reject")
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    def test_reject_terminal_returns_409(self, client, storage):
        ids = _seed(storage, count=1, status="rejected")
        resp = client.post(f"/api/cvg/ripples/{ids[0]}/reject")
        assert resp.status_code == 409


class TestGetRippleStats:
    def test_stats_returns_count_by_status_and_volume(self, client, storage):
        _seed(storage, count=2, status="pending")
        _seed(storage, count=1, status="applied")
        resp = client.get("/api/cvg/ripples/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["by_status"]["pending"] == 2
        assert data["by_status"]["applied"] == 1
        assert data["total"] == 3

    def test_pydantic_schema_importable(self):
        """Phase 9.13: 4 Pydantic schemas in dashboard.protocols."""
        assert RippleListItemResponse is not None
        assert RippleDetailResponse is not None
        assert RippleActionResponse is not None
        assert RippleStatsResponse is not None
