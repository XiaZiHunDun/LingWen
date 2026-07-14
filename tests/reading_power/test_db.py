"""Tests for ReadingPowerDB."""

import pytest

from infra.reading_power.db import ReadingPowerDB


class TestReadingPowerDB:
    """Test suite for ReadingPowerDB."""

    def test_save_and_get_hook(self, temp_db: ReadingPowerDB) -> None:
        """Save a hook and verify retrieval."""
        # Save a hook
        hook_id = temp_db.save_hook(
            chapter="ch001",
            hook_type="conflict",
            strength=0.85,
            position="opening",
            content="主角被困在即将崩塌的洞穴中",
            llm_analyzed=True,
        )
        assert hook_id > 0

        # Retrieve hooks
        hooks = temp_db.get_hooks("ch001")
        assert len(hooks) == 1

        hook = hooks[0]
        assert hook["chapter"] == "ch001"
        assert hook["hook_type"] == "conflict"
        assert hook["strength"] == 0.85
        assert hook["position"] == "opening"
        assert hook["content"] == "主角被困在即将崩塌的洞穴中"
        assert hook["llm_analyzed"] == 1

    def test_save_and_get_coolpoint(self, temp_db: ReadingPowerDB) -> None:
        """Save a coolpoint and verify retrieval."""
        # Save a coolpoint
        cp_id = temp_db.save_coolpoint(
            chapter="ch001",
            pattern="反杀",
            density=0.75,
            combo_with="觉醒,爆发",
            content="主角在绝境中爆发出隐藏力量，一击反杀",
            llm_analyzed=False,
        )
        assert cp_id > 0

        # Retrieve coolpoints
        coolpoints = temp_db.get_coolpoints("ch001")
        assert len(coolpoints) == 1

        cp = coolpoints[0]
        assert cp["chapter"] == "ch001"
        assert cp["pattern"] == "反杀"
        assert cp["density"] == 0.75
        assert cp["combo_with"] == "觉醒,爆发"
        assert cp["content"] == "主角在绝境中爆发出隐藏力量，一击反杀"
        assert cp["llm_analyzed"] == 0

    def test_update_and_get_chapter_summary(self, temp_db: ReadingPowerDB) -> None:
        """Update chapter summary and verify values."""
        # Update summary
        temp_db.update_chapter_summary(
            chapter="ch001",
            hook_count=3,
            hook_strength_avg=0.82,
            coolpoint_count=5,
            coolpoint_density=0.68,
            reading_power_score=0.75,
        )

        # Retrieve summary
        summary = temp_db.get_chapter_summary("ch001")
        assert summary is not None
        assert summary["chapter"] == "ch001"
        assert summary["hook_count"] == 3
        assert summary["hook_strength_avg"] == 0.82
        assert summary["coolpoint_count"] == 5
        assert summary["coolpoint_density"] == 0.68
        assert summary["reading_power_score"] == 0.75
        assert summary["last_analyzed_at"] is not None

    def test_multiple_hooks_same_chapter(self, temp_db: ReadingPowerDB) -> None:
        """Save multiple hooks for same chapter and verify retrieval."""
        # Save multiple hooks
        temp_db.save_hook("ch002", "mystery", 0.9, "opening", "神秘信号的来源是什么？")
        temp_db.save_hook("ch002", "conflict", 0.8, "mid", "两股势力在暗中对峙")
        temp_db.save_hook("ch002", "cliffhanger", 0.95, "ending", "主角发现了惊天秘密")

        hooks = temp_db.get_hooks("ch002")
        assert len(hooks) == 3

        # Verify ordering (by position, then id)
        positions = [h["position"] for h in hooks]
        assert positions == ["opening", "mid", "ending"]

    def test_replace_existing_hook(self, temp_db: ReadingPowerDB) -> None:
        """Test that saving same hook type/position replaces existing."""
        # Save initial hook
        temp_db.save_hook("ch003", "conflict", 0.7, "opening", "Initial content")

        # Replace with new content
        temp_db.save_hook("ch003", "conflict", 0.9, "opening", "Updated content")

        hooks = temp_db.get_hooks("ch003")
        assert len(hooks) == 1
        assert hooks[0]["strength"] == 0.9
        assert hooks[0]["content"] == "Updated content"

    def test_chapter_summary_update(self, temp_db: ReadingPowerDB) -> None:
        """Test updating chapter summary multiple times."""
        # First update
        temp_db.update_chapter_summary(
            chapter="ch004",
            hook_count=2,
            hook_strength_avg=0.6,
            coolpoint_count=3,
            coolpoint_density=0.5,
        )

        # Second update with higher values
        temp_db.update_chapter_summary(
            chapter="ch004",
            hook_count=5,
            hook_strength_avg=0.85,
            coolpoint_count=8,
            coolpoint_density=0.72,
            reading_power_score=0.78,
        )

        summary = temp_db.get_chapter_summary("ch004")
        assert summary["hook_count"] == 5
        assert summary["hook_strength_avg"] == 0.85
        assert summary["coolpoint_count"] == 8
        assert summary["coolpoint_density"] == 0.72
        assert summary["reading_power_score"] == 0.78

    def test_nonexistent_chapter_returns_empty(self, temp_db: ReadingPowerDB) -> None:
        """Test that getting hooks/coolpoints for nonexistent chapter returns empty."""
        assert temp_db.get_hooks("nonexistent") == []
        assert temp_db.get_coolpoints("nonexistent") == []
        assert temp_db.get_chapter_summary("nonexistent") is None
