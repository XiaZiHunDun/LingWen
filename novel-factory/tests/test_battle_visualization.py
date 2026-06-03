#!/usr/bin/env python3
"""Tests for BattleVisualizationChecker"""
import sys
from pathlib import Path

import pytest

# Ensure project root (novel-factory/) is in sys.path
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from infra.consistency.checkers.battle_visualization import BattleVisualizationChecker
from infra.consistency.engine.data_structures import IssueSeverity


class TestBattleVisualizationChecker:
    """BattleVisualizationChecker Tests"""

    def setup_method(self):
        self.checker = BattleVisualizationChecker()

    def test_is_battle_scene(self):
        """Test battle scene detection"""
        battle_content = "林夜与敌人战斗，剑光交错，招式凌厉。"
        assert self.checker._is_battle_scene(battle_content) is True

    def test_is_not_battle_scene(self):
        """Test non-battle scene"""
        normal_content = "林夜站在星空下，心中思绪万千。"
        assert self.checker._is_battle_scene(normal_content) is False

    def test_extract_battle_paragraphs(self):
        """Test battle paragraph extraction"""
        content = """
        林夜看着远方的星空，心中感慨。

        战斗中，林夜的剑光闪烁，能量波动剧烈。

        苏琳静静站在那里，眼眶泛红。
        """
        paragraphs = self.checker._extract_battle_paragraphs(content)

        assert len(paragraphs) >= 1

    def test_excessive_abstract_p2(self):
        """Test excessive abstract - P2"""
        content = """
        战斗中，星辰能量在体内涌动，能量波动剧烈。
        虚无的力量在空间中流转，神秘力量汇聚。
        某种力量驱使着他，能量不断爆发。
        灵气充斥着整个战场，气场强大无比。
        """

        issues = self.checker.check(content, 45, {})

        abstract_issues = [i for i in issues if i.issue_type == "excessive_abstract_battle"]
        assert len(abstract_issues) >= 1
        assert abstract_issues[0].severity == IssueSeverity.P2

    def test_concrete_visual_good(self):
        """Test concrete visual good"""
        content = """
        战斗中，剑身发出炽白光，火星四溅。
        敌人的血喷涌而出，染红了地面。
        碎片飞溅，尘埃弥漫，战斗声响彻战场。
        """

        issues = self.checker.check(content, 45, {})

        assert len(issues) == 0

    def test_calculate_abstract_ratio(self):
        """Test abstract ratio calculation"""
        abstract_content = """
        星辰能量涌动，虚无的力量在流转。
        神秘力量汇聚，灵气充斥。
        """

        ratio = self.checker.calculate_abstract_ratio(abstract_content)

        assert ratio > 0.6

    def test_mixed_content_ratio(self):
        """Test mixed content ratio"""
        mixed_content = """
        战斗中，剑身发出炽白光，能量波动剧烈。
        火星四溅，虚无的力量在流转。
        碎片飞溅，神秘力量汇聚。
        """

        ratio = self.checker.calculate_abstract_ratio(mixed_content)

        assert 0.3 < ratio < 0.7

    def test_non_battle_scene_no_issues(self):
        """Test non-battle scene no issues"""
        content = "林夜站在星空下，心中思绪万千。"

        issues = self.checker.check(content, 45, {})

        assert len(issues) == 0
