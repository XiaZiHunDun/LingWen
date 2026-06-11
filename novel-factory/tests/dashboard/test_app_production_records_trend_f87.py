"""Phase 9.96 F87: GET /api/production-records/trend."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from dashboard.app import create_app


class TestProductionTrendApiF87:
    def test_trend_endpoint(self, tmp_path: Path, monkeypatch) -> None:
        records_dir = tmp_path / "pilot_records"
        records_dir.mkdir()
        (records_dir / "ch360.json").write_text(
            json.dumps({
                "pilot_id": "p360",
                "chapter_num": 360,
                "run": {"total_cost_usd": 0.025},
                "recorded_at": "2026-06-11T00:00:00Z",
            }),
            encoding="utf-8",
        )
        (records_dir / "batch-361-363.json").write_text(
            json.dumps({
                "batch_id": "b1",
                "start_chapter": 361,
                "chapters_attempted": 3,
                "total_cost_usd": 0.083,
                "stopped_reason": "completed",
                "recorded_at": "2026-06-11T01:00:00Z",
            }),
            encoding="utf-8",
        )
        monkeypatch.setenv("LINGWEN_PILOT_RECORDS_DIR", str(records_dir))

        app = create_app(db_path=tmp_path / "rp.db")
        client = TestClient(app)
        resp = client.get("/api/production-records/trend")
        assert resp.status_code == 200
        body = resp.json()
        assert body["point_count"] == 2
        assert body["total_cost_usd"] == 0.108
        assert body["points"][0]["label"] == "ch360"
        assert body["points"][0]["incremental_cost_usd"] == 0.025
        assert body["points"][1]["label"] == "ch361-363"
        assert body["points"][1]["cumulative_cost_usd"] == 0.108
