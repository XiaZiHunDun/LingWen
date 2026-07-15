"""Phase 9.82 F74: production_records scanner."""
from __future__ import annotations

import json

import pytest

from infra.agent_system.production_records import (
    compute_deduplicated_cost_usd,
    list_production_records,
    parse_record_file,
    production_cost_trend,
    rollup_production_records,
)


class TestProductionRecords:
    def test_parse_pilot_json(self, tmp_path):
        path = tmp_path / "ch360.json"
        path.write_text(
            json.dumps({
                "pilot_id": "p1",
                "chapter_num": 360,
                "operator": "tester",
                "recorded_at": "2026-06-11T00:00:00Z",
                "env": {"primary_provider": "minimax"},
                "run": {
                    "emit_chapter_completed": True,
                    "total_cost_usd": 0.025,
                },
                "hooks": {"memory_context_source": "stub"},
            }),
            encoding="utf-8",
        )
        item = parse_record_file(path)
        assert item is not None
        assert item.chapter_num == 360
        assert item.provider == "minimax"
        assert item.emit_chapter_completed is True

    def test_parse_batch_json(self, tmp_path):
        path = tmp_path / "batch-361-363.json"
        path.write_text(
            json.dumps({
                "batch_id": "b1",
                "start_chapter": 361,
                "chapters_attempted": 3,
                "chapters_succeeded": 3,
                "total_cost_usd": 0.08,
                "stopped_reason": "completed",
                "recorded_at": "2026-06-11T01:00:00Z",
            }),
            encoding="utf-8",
        )
        item = parse_record_file(path)
        assert item is not None
        assert item.record_type == "batch"
        assert item.chapter_range == "361-363"

    def test_list_filter_by_chapter(self, tmp_path):
        (tmp_path / "ch360.json").write_text(
            json.dumps({"pilot_id": "a", "chapter_num": 360, "run": {}}),
            encoding="utf-8",
        )
        (tmp_path / "ch361.json").write_text(
            json.dumps({"pilot_id": "b", "chapter_num": 361, "run": {}}),
            encoding="utf-8",
        )
        items = list_production_records(tmp_path, chapter_num=360, limit=10)
        assert len(items) == 1
        assert items[0].chapter_num == 360

    def test_rollup_deduplicates_batch_and_pilot_cost(self, tmp_path):
        (tmp_path / "ch360.json").write_text(
            json.dumps({
                "pilot_id": "p360",
                "chapter_num": 360,
                "run": {"total_cost_usd": 0.025},
            }),
            encoding="utf-8",
        )
        (tmp_path / "batch-361-363.json").write_text(
            json.dumps({
                "batch_id": "b1",
                "start_chapter": 361,
                "chapters_attempted": 3,
                "total_cost_usd": 0.083,
                "stopped_reason": "completed",
                "recorded_at": "2026-06-11T02:00:00Z",
            }),
            encoding="utf-8",
        )
        (tmp_path / "ch361.json").write_text(
            json.dumps({
                "pilot_id": "p361",
                "chapter_num": 361,
                "run": {"total_cost_usd": 0.025},
            }),
            encoding="utf-8",
        )
        records = list_production_records(tmp_path, limit=10)
        assert compute_deduplicated_cost_usd(records) == pytest.approx(0.108)
        rollup = rollup_production_records(tmp_path, limit=10)
        assert rollup["total_cost_usd"] == pytest.approx(0.108)
        assert rollup["chapters_with_records"] == 4
        assert rollup["batch_count"] == 1
        assert len(rollup["batches"]) == 1

    def test_production_cost_trend_time_order_and_dedup(self, tmp_path):
        (tmp_path / "ch360.json").write_text(
            json.dumps({
                "pilot_id": "p360",
                "chapter_num": 360,
                "run": {"total_cost_usd": 0.025},
                "recorded_at": "2026-06-11T00:00:00Z",
            }),
            encoding="utf-8",
        )
        (tmp_path / "batch-361-363.json").write_text(
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
        (tmp_path / "ch361.json").write_text(
            json.dumps({
                "pilot_id": "p361",
                "chapter_num": 361,
                "run": {"total_cost_usd": 0.025},
                "recorded_at": "2026-06-11T02:00:00Z",
            }),
            encoding="utf-8",
        )
        trend = production_cost_trend(tmp_path, limit=10)
        assert trend["point_count"] == 3
        assert trend["total_cost_usd"] == pytest.approx(0.108)
        labels = [p["label"] for p in trend["points"]]
        assert labels == ["ch360", "ch361-363", "ch361"]
        assert trend["points"][0]["incremental_cost_usd"] == pytest.approx(0.025)
        assert trend["points"][1]["incremental_cost_usd"] == pytest.approx(0.083)
        assert trend["points"][2]["incremental_cost_usd"] == pytest.approx(0.0)
        assert trend["points"][2]["cumulative_cost_usd"] == pytest.approx(0.108)
