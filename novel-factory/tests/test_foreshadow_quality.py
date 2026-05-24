#!/usr/bin/env python3
"""Tests for ForeshadowQualityChecker"""
import pytest
import sys
from pathlib import Path

# Ensure project root (novel-factory/) is in sys.path
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from infra.consistency.checkers.foreshadow_quality import ForeshadowQualityChecker
from infra.consistency.engine.data_structures import IssueSeverity


class TestForeshadowQualityChecker:
    """ForeshadowQualityChecker Tests"""

    def setup_method(self):
        self.checker = ForeshadowQualityChecker()

    def test_count_mechanical_suspense(self):
        """Test mechanical suspense count"""
        content = "但他不知道的是就在这时突然下一秒谁也不知道发生了什么"
        count = self.checker._count_mechanical_suspense(content)

        # Contains: 但他不知道的是, 就在这时, 突然, 下一秒, 谁也不知道
        assert count >= 4

    def test_no_mechanical_suspense(self):
        """Test no mechanical suspense"""
        content = "林夜看着远方的星空，心中思绪万千。"
        count = self.checker._count_mechanical_suspense(content)

        assert count == 0

    def test_high_density_p2(self):
        """Test high mechanical suspense density - P2"""
        content = """
        但他不知道的是，就在这时，意外发生了。
        下一秒，谁也不知道接下来会发生什么。
        而此刻，讽刺的是，事情朝着最坏的方向发展。
        但她不知道的是，危机正在逼近。
        下一秒，战斗开始了。
        就在这时，变故突生。
        谁也不知道下一秒会发生什么。
        """

        issues = self.checker.check(content, 1, {})

        density_issues = [i for i in issues if i.issue_type == "mechanical_suspense_density"]
        assert len(density_issues) >= 1

    def test_good_foreshadow_no_issues(self):
        """Test good foreshadow no issues"""
        content = """
        林夜站在星空下，想起小时候父亲教他辨认星辰的日子。
        那时候的他还不知道，这些星辰将在未来决定他的命运。
        """

        issues = self.checker.check(content, 1, {})

        assert len(issues) == 0

    def test_detect_specific_mechanical(self):
        """Test specific mechanical detection"""
        content = "但他不知道的是，事情正在起变化。"
        mentions = self.checker._detect_specific_mechanical(content, 1)

        assert len(mentions) >= 1
        assert mentions[0]["pattern"] == "但他不知道的是"