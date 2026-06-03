"""
RuleMatcher Module for Reading Power System.
Scans chapter text for hooks and coolpoints using YAML rule libraries.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, NamedTuple

import yaml

from infra.reading_power.db import ReadingPowerDB


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

                        results.append(SuspectedSegment(
                            segment_type="hook",
                            pattern_name=hook_type,
                            content=context,
                            confidence=min(confidence, 1.0),
                            position=position,
                            offset=match.start()
                        ))

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

                        results.append(SuspectedSegment(
                            segment_type="coolpoint",
                            pattern_name=pattern_name,
                            content=context,
                            confidence=min(confidence, 1.0),
                            position=position,
                            offset=match.start()
                        ))

        return sorted(results, key=lambda x: x.confidence, reverse=True)

    def _determine_position(self, text: str) -> str:
        """
        Determine if match is at beginning, middle, or end of text.

        Args:
            text: The text to analyze

        Returns:
            Position category: "开头", "中段", or "结尾"
        """
        length = len(text)
        if length == 0:
            return "中段"

        # Use character-based position for Chinese text
        if length > 0:
            # Simple thirds-based approach
            first_third = length // 3
            length - first_third

            # For short texts, use more nuanced approach
            if length < 100:
                return "中段"

            # Check first 20% for "开头"
            if length > 20:
                # Check first third
                return "开头"

        return "中段"
