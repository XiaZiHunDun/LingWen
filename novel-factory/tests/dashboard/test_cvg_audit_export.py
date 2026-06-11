"""Phase 9.60 F51: ripple audit export CSV/JSON."""
from __future__ import annotations

import csv
import io
import json

import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_app
from infra.cross_volume.ripple import CrossVolumeRipple
from infra.cross_volume.storage import RippleStorage


@pytest.fixture
def storage_with_ripple(tmp_path):
    storage = RippleStorage(db_path=tmp_path / "export.db")
    ripple = CrossVolumeRipple(
        id="rip-export-1",
        trigger_volume=1,
        trigger_chapter=1,
        status="applied",
    )
    storage.append_ripple(ripple)
    return storage, ripple.id


@pytest.fixture
def client(storage_with_ripple, monkeypatch):
    storage, _ = storage_with_ripple
    from dashboard import app as app_module
    monkeypatch.setattr(app_module, "_default_storage", lambda: storage)
    return TestClient(create_app())


class TestRippleAuditExport:
    def test_export_json(self, client, storage_with_ripple):
        _, rid = storage_with_ripple
        resp = client.get(f"/api/cvg/ripples/{rid}/audit/export?format=json")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        data = json.loads(resp.text)
        assert isinstance(data, list)
        assert data[0]["action"] == "created"
        assert data[0]["ripple_id"] == rid

    def test_export_csv(self, client, storage_with_ripple):
        _, rid = storage_with_ripple
        resp = client.get(f"/api/cvg/ripples/{rid}/audit/export?format=csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        rows = list(csv.DictReader(io.StringIO(resp.text)))
        assert len(rows) >= 1
        assert rows[0]["action"] == "created"
        assert rows[0]["ripple_id"] == rid

    def test_export_404_missing_ripple(self, client):
        resp = client.get("/api/cvg/ripples/rip-missing/audit/export")
        assert resp.status_code == 404

    def test_export_invalid_format_422(self, client, storage_with_ripple):
        _, rid = storage_with_ripple
        resp = client.get(f"/api/cvg/ripples/{rid}/audit/export?format=xml")
        assert resp.status_code == 422

    def test_export_respects_limit(self, client, storage_with_ripple):
        _, rid = storage_with_ripple
        resp = client.get(f"/api/cvg/ripples/{rid}/audit/export?format=json&limit=1")
        assert len(json.loads(resp.text)) == 1
