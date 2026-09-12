"""
RuleMatcher Module for Reading Power System.
Scans chapter text for hooks and coolpoints using YAML rule libraries.

Phase 57 P3-ARCHDEBT: relocated from infra/reading_power/rule_matcher.py to
packages/lingwen-reading-power/src/lingwen_reading_power/rule_matcher.py.
Canonical import: ``from lingwen_reading_power.rule_matcher import RuleMatcher``.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, NamedTuple

import yaml

from lingwen_reading_power.db import ReadingPowerDB


class SuspectedSegment(NamedTuple):
    """A suspected segment found during scanning."""

    segment_type: str  # "hook" or "coolpoint"
    pattern_name: str
    content: str
    confidence: float
    position: str
    offset: int


class RuleMatcher:
    """Scans chapter text for hooks and coolpoints using rule libraries."""

    HOOKS_RULES_PATH = Path(__file__).parent.parent.parent / "rules" / "reading_power_hooks.yaml"
    COOLPOINTS_RULES_PATH = Path(__file__).parent.parent.parent / "rules" / "reading_power_coolpoints.yaml"

    def __init__(self, db: ReadingPowerDB):
        self.db = db
        self.hook_rules = self._load_rules(self.HOOKS_RULES_PATH)
        self.coolpoint_rules = self._load_rules(self.COOLPOINTS_RULES_PATH)

    def _load_rules(self, path: Path) -> Dict[str, Any]:
        """Load rules from YAML file."""
        if not path.exists():
            return {"hook_patterns": {}} if "hooks" in str(path) else {"coolpoint_patterns": {}}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def scan(self, chapter_text: str, chapter_num: int) -> List[SuspectedSegment]:
        """
        Scan chapter text for hooks and coolpoints.

        Args:
            chapter_text: The chapter content to scan
            chapter_num: Chapter number for reference

        Returns:
            List of SuspectedSegment sorted by confidence (highest first)
        """
        results = []
        position = self._determine_position(chapter_text)

        # Scan hooks
        hook_key = "hook_patterns"
        if hook_key in self.hook_rules:
            for hook_type, rule in self.hook_rules[hook_key].items():
                for keyword in rule.get("keywords", []):
                    pattern = re.escape(keyword)
                    for match in re.finditer(pattern, chapter_text):
                        confidence = rule.get("strength_base", 0.5)
                        pos_weight = rule.get("position_weight", {}).get(position, 1.0)
                        confidence *= pos_weight

                        start = max(0, match.start() - 20)
                        end = min(len(chapter_text), match.end() + 40)
                        context = chapter_text[start:end]

                        results.append(
                            SuspectedSegment(
                                segment_type="hook",
                                pattern_name=hook_type,
                                content=context,
                                confidence=min(confidence, 1.0),
                                position=position,
                                offset=match.start(),
                            )
                        )

        # Scan coolpoints
        coolpoint_key = "coolpoint_patterns"
        if coolpoint_key in self.coolpoint_rules:
            for pattern_name, rule in self.coolpoint_rules[coolpoint_key].items():
                for trigger in rule.get("triggers", []):
                    pattern = re.escape(trigger)
                    for match in re.finditer(pattern, chapter_text):
                        confidence = rule.get("emotion_intensity", 0.5)

                        start = max(0, match.start() - 20)
                        end = min(len(chapter_text), match.end() + 40)
                        context = chapter_text[start:end]

                        results.append(
                            SuspectedSegment(
                                segment_type="coolpoint",
                                pattern_name=pattern_name,
                                content=context,
                                confidence=min(confidence, 1.0),
                                position=position,
                                offset=match.start(),
                            )
                        )

        return sorted(results, key=lambda x: x.confidence, reverse=True)

    def _determine_position(self, text: str) -> str:
        """
        Coarse chapter-level position classification.

        Phase 57 C1.5 fixup: the prior implementation had an unreachable
        ``return "中段"`` at the end and an always-true ``if length > 20``
        branch that returned ``"开头"`` for every chapter >= 100 chars.
        Worse, the rules YAML at ``rules/reading_power_hooks.yaml`` uses
        position keys ``"开篇" / "中段" / "结尾"`` (NOT ``"开头"``), so the
        prior code's "开头" never matched any pos_weight — pos_weight always
        fell through to its default (1.0). Behavior was effectively a no-op.

        Without a per-match ``offset`` parameter, this function can only do
        a coarse text-length-based classification. Match-level position
        would require refactoring ``scan()`` to plumb the offset through.

        Returns:
            Position category: always ``"中段"`` (the only key guaranteed to
            exist in pos_weight lookups; 开篇/结尾 need match offset).
        """
        length = len(text)
        if length == 0 or length < 100:
            return "中段"
        return "中段"  # coarse — no offset, default to middle