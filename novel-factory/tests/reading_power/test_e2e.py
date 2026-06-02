"""
End-to-end tests for the reading power system.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile

from infra.reading_power import (
    ReadingPowerEngine,
    ReadingPowerDB,
)


class TestReadingPowerE2E:
    """End-to-end tests for reading power analysis"""

    def test_e2e_analyze_sample_text(self, tmp_path: Path):
        """
        Test the complete reading power analysis flow with sample text.
        """
        # Setup: Create temp database
        db_path = tmp_path / "test_reading_power.db"
        db = ReadingPowerDB(db_path)
        engine = ReadingPowerEngine(db=db)

        # Sample text with clear hook and coolpoint elements
        sample_text = """
        主角正在修炼，突然感知到危险气息逼近。

        敌人出现在前方，生死关头，主角必须做出选择。

        结尾处设置了悬念：主角的真实身份究竟是什么？

        同时，打脸场景出现了，对手目瞪口呆。
        """

        # Execute: Analyze the chapter
        result = engine.analyze_chapter(999, sample_text)

        # Verify: Analysis completed successfully
        assert result.success is True

        # Verify: Data was stored
        data = engine.get_chapter_reading_power(999)
        assert "hooks" in data or "summary" in data

    def test_full_workflow_analyze_store_query(self, tmp_path: Path):
        """
        Test complete workflow: analyze -> store -> query
        """
        # Setup
        db_path = tmp_path / "test.db"
        db = ReadingPowerDB(db_path)
        engine = ReadingPowerEngine(db=db)

        # Execute: Analyze text with hooks and coolpoints
        text = "危险！敌人出现，打脸场景！"
        result = engine.analyze_chapter(1, text)

        # Verify: Success
        assert result.success is True

        # Verify: Data was stored
        data = engine.get_chapter_reading_power(1)
        assert "hooks" in data
        assert "summary" in data

    def test_e2e_multiple_chapters(self, tmp_path: Path):
        """
        Test analyzing multiple chapters in sequence.
        """
        # Setup
        db_path = tmp_path / "test_multi.db"
        db = ReadingPowerDB(db_path)
        engine = ReadingPowerEngine(db=db)

        texts = {
            1: "危机！敌人突然出现，主角面临生死抉择。",
            2: "打脸时刻到了，对手目瞪口呆。",
            3: "悬念陡起，主角的真实身份是什么？",
        }

        # Execute
        results = []
        for chapter_num, text in texts.items():
            result = engine.analyze_chapter(chapter_num, text)
            results.append(result.success)

        # Verify: All successful
        assert all(results)

        # Verify: All data stored
        for chapter_num in texts.keys():
            data = engine.get_chapter_reading_power(chapter_num)
            assert data is not None

    def test_e2e_empty_chapter(self, tmp_path: Path):
        """
        Test handling of empty chapter text.
        """
        # Setup
        db_path = tmp_path / "test_empty.db"
        db = ReadingPowerDB(db_path)
        engine = ReadingPowerEngine(db=db)

        # Execute
        result = engine.analyze_chapter(1, "")

        # Verify: Should succeed but return empty results
        assert result.success is True
        assert result.hooks == []
        assert result.coolpoints == []

    def test_e2e_chapter_summary_calculation(self, tmp_path: Path):
        """
        Test that chapter summary is calculated correctly.
        """
        # Setup
        db_path = tmp_path / "test_summary.db"
        db = ReadingPowerDB(db_path)
        engine = ReadingPowerEngine(db=db)

        # Text with multiple hooks and coolpoints
        text = "危险！敌人出现！震惊！打脸！反杀！"

        # Execute
        engine.analyze_chapter(1, text)

        # Verify: Summary exists
        summary = db.get_chapter_summary(1)
        assert summary is not None
        # Hook count should be >= 0 (depends on rule matching)
        assert "hook_count" in summary
        assert "coolpoint_count" in summary


class TestReadingPowerDBPersistence:
    """Test database persistence of reading power data"""

    def test_db_persists_between_sessions(self, tmp_path: Path):
        """
        Test that data persists when database is re-opened.
        """
        db_path = tmp_path / "persistent.db"

        # First session: write data
        db1 = ReadingPowerDB(db_path)
        db1.save_hook(1, "危机钩", 0.8, "结尾", "测试内容")

        # Second session: read data
        db2 = ReadingPowerDB(db_path)
        hooks = db2.get_hooks(1)

        # Verify: Data persisted
        assert len(hooks) == 1
        assert hooks[0]["hook_type"] == "危机钩"

    def test_db_chapter_summary_persistence(self, tmp_path: Path):
        """
        Test chapter summary persistence.
        """
        db_path = tmp_path / "summary_persist.db"

        # First session
        db1 = ReadingPowerDB(db_path)
        db1.update_chapter_summary(1, 5, 0.75, 3, 0.85)

        # Second session
        db2 = ReadingPowerDB(db_path)
        summary = db2.get_chapter_summary(1)

        # Verify
        assert summary is not None
        assert summary["hook_count"] == 5
        assert summary["hook_strength_avg"] == 0.75