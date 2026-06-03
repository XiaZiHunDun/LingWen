#!/usr/bin/env python3
"""Tests for ScenePatternRepeatChecker"""
import sys
from pathlib import Path

import pytest

# Ensure project root (novel-factory/) is in sys.path
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from infra.consistency.checkers.scene_pattern_repeat import ScenePatternRepeatChecker
from infra.consistency.engine.data_structures import IssueSeverity


class TestScenePatternRepeatChecker:
    """ScenePatternRepeatChecker Tests"""

    def setup_method(self):
        self.checker = ScenePatternRepeatChecker()

    def test_detect_starry_night_scene(self):
        """Test starry night scene detection"""
        content = "他们并肩坐在草地上，看星星聊天，星空很美，星光点点。"
        label = self.checker._detect_scene_label(content)
        assert label == "星空对话"

    def test_detect_ruins_scene(self):
        """Test ruins scene detection"""
        content = "废墟中到处是残垣断壁，他们小心翼翼地探索着遗迹。"
        label = self.checker._detect_scene_label(content)
        assert label == "废墟探索"

    def test_no_scene_label(self):
        """Test no scene label"""
        content = "林夜站在原地，心中有些犹豫。"
        label = self.checker._detect_scene_label(content)
        assert label is None

    def test_consecutive_scene_repeat_p0(self):
        """Test consecutive scene repeat - P0 level"""
        context = {
            "recent_scene_labels": ["星空对话", "星空对话", "星空对话"]
        }
        content = "他们再次来到草地上看星星，星空依然美丽。"

        issues = self.checker.check(content, 45, context)

        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.P0
        assert "星空对话" in issues[0].title

    def test_no_repeat_within_threshold(self):
        """Test no repeat within threshold"""
        context = {
            "recent_scene_labels": ["星空对话", "废墟探索"]
        }
        content = "废墟中到处是残垣断壁，他们小心翼翼地探索着遗迹。"

        issues = self.checker.check(content, 45, context)

        assert len(issues) == 0

    def test_first_chapter_no_history(self):
        """Test first chapter no history"""
        context = {}
        content = "他们并肩坐在草地上，看星星聊天。"

        issues = self.checker.check(content, 1, context)

        assert len(issues) == 0

    def test_get_scene_label_public_interface(self):
        """Test public interface"""
        content = "他们并肩坐在草地上，看星星聊天，星空很美。"
        label = self.checker.get_scene_label(content)
        assert label == "星空对话"
