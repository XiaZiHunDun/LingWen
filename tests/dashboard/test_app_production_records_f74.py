"""Phase 9.82 F74: GET /api/production-records."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from dashboard.app import create_app


class TestProductionRecordsApiF74:
    def test_list_production_records(self, tmp_path: Path, monkeypatch) -> None:
        records_dir = tmp_path / "pilot_records"
        records_dir.mkdir()
        (records_dir / "ch360.json").write_text(
            json.dumps({
                "pilot_id": "p360",
                "chapter_num": 360,
                "operator": "op",
                "recorded_at": "2026-06-11T00:00:00Z",
                "env": {"primary_provider": "minimax"},
                "run": {"emit_chapter_completed": True, "total_cost_usd": 0.03},
                "hooks": {"memory_context_source": "stub"},
            }),
            encoding="utf-8",
        )
        monkeypatch.setenv("LINGWEN_PILOT_RECORDS_DIR", str(records_dir))

        app = create_app(db_path=tmp_path / "rp.db")
        client = TestClient(app)
        resp = client.get("/api/production-records")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["records"]) == 1
        assert body["records"][0]["chapter_num"] == 360
        assert body["records"][0]["provider"] == "minimax"

    def test_empty_dir(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setenv("LINGWEN_PILOT_RECORDS_DIR", str(tmp_path / "missing"))
        app = create_app(db_path=tmp_path / "rp.db")
        client = TestClient(app)
        resp = client.get("/api/production-records")
        assert resp.status_code == 200
        assert resp.json()["records"] == []
