"""Phase 9.89 F81: GET /api/production-records/rollup."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from dashboard.app import create_app


class TestProductionRollupApiF81:
    def test_rollup_endpoint(self, tmp_path: Path, monkeypatch) -> None:
        records_dir = tmp_path / "pilot_records"
        records_dir.mkdir()
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
        resp = client.get("/api/production-records/rollup")
        assert resp.status_code == 200
        body = resp.json()
        assert body["batch_count"] == 1
        assert body["total_cost_usd"] == 0.083
        assert len(body["batches"]) == 1
        assert body["batches"][0]["chapter_range"] == "361-363"
