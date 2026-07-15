"""Tests for chapter_production_retry."""
from pathlib import Path

from infra.agent_system.chapter_production_retry import chapters_needing_retry


def test_retry_skips_failed_batch_when_body_exists(tmp_path):
    chapters_dir = tmp_path / "chapters"
    chapters_dir.mkdir()
    (chapters_dir / "ch007.md").write_text("x" * 500, encoding="utf-8")
    summary = tmp_path / "batch.json"
    summary.write_text(
        '{"chapters": [{"chapter_num": 7, "emit_chapter_completed": false}]}',
        encoding="utf-8",
    )
    assert chapters_needing_retry(
        6, 7, chapters_dir=chapters_dir, batch_summary_path=summary,
    ) == [6]
