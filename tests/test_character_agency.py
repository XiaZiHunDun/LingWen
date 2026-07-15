#!/usr/bin/env python3
"""Tests for CharacterAgencyChecker"""
import sys
from pathlib import Path

import pytest

# Ensure project root is in sys.path
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from infra.consistency.checkers.character_agency import CharacterAgencyChecker
from infra.consistency.engine.data_structures import IssueSeverity


class TestCharacterAgencyChecker:
    """CharacterAgencyChecker Tests"""

    def setup_method(self):
        self.checker = CharacterAgencyChecker()

    def test_count_reactive_patterns(self):
        """Test reactive pattern count"""
        content = """
        苏琳静静站在那里，眼眶泛红，泪水模糊了视线。
        她默默低下头，轻轻叹了口气。
        """
        count = self.checker._count_patterns(content, "苏琳", self.checker.REACTIVE_PATTERNS)

        assert count >= 3

    def test_count_active_patterns(self):
        """Test active pattern count"""
        content = """
        林夜站起身来，大步走向前方。
        他毫不犹豫地决定攻击，径直冲向敌人。
        """
        count = self.checker._count_patterns(content, "林夜", self.checker.ACTIVE_PATTERNS)

        assert count >= 4

    def test_low_agency_ratio_p1(self):
        """Test low agency ratio - P1"""
        context = {"target_characters": ["苏琳"]}
        content = """
        苏琳静静站在那里，眼眶泛红，泪水模糊了视线。
        她默默低下头，轻轻叹息。
        她感到心中一紧，似乎有什么不好的预感。
        只是微微一笑，没有说话。
        """

        issues = self.checker.check(content, 45, context)

        agency_issues = [i for i in issues if i.issue_type == "low_character_agency"]
        assert len(agency_issues) >= 1
        assert agency_issues[0].severity in [IssueSeverity.P1, IssueSeverity.P2]

    def test_good_agency_ratio(self):
        """Test good agency ratio"""
        context = {"target_characters": ["林夜"]}
        content = """
        林夜站起身来，大步走向前方。
        他毫不犹豫地决定攻击，径直冲向敌人。
        他抬起手，指向前方。
        他迈步跨出，挣脱束缚。
        她静静看着，但没什么感觉。
        """

        issues = self.checker.check(content, 45, context)

        agency_issues = [i for i in issues if i.issue_type == "low_character_agency"]
        assert len(agency_issues) == 0

    def test_calculate_agency_ratio(self):
        """Test agency ratio calculation"""
        content = """
        林夜站起身来，大步走向前方。
        他毫不犹豫地决定攻击，径直冲向敌人。
        她静静看着远方。
        """
        ratio = self.checker.calculate_agency_ratio(content, "林夜")

        assert ratio >= 1.0

    def test_no_reactive_no_issues(self):
        """Test no reactive no issues"""
        context = {"target_characters": ["林夜"]}
        content = """
        林夜站起身来，大步走向前方。
        他毫不犹豫地决定攻击，径直冲向敌人。
        """

        issues = self.checker.check(content, 45, context)

        agency_issues = [i for i in issues if i.issue_type == "low_character_agency"]
        assert len(agency_issues) == 0

    def test_get_character_paragraphs(self):
        """Test character paragraphs extraction"""
        content = """
        林夜看着远方的星空，心中感慨。

        苏琳静静站在那里，眼眶泛红。

        林夜站起身来，决定离开。
        """
        paragraphs = self.checker._get_character_paragraphs(content, "林夜")

        assert len(paragraphs) == 2
