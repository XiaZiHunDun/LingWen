"""Phase 9.82 F74: production_records scanner."""
from __future__ import annotations

import json

import pytest

from infra.agent_system.production_records import (
    list_production_records,
    parse_record_file,
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
