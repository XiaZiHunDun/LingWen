"""
CoolPointTracker for the reading power system (追读力系统).
Tracks and retrieves cool points from chapters.
"""

import json
from typing import Any, Dict, List, Tuple

from infra.reading_power.db import ReadingPowerDB


class CoolPointTracker:
    """Tracker for cool points (爽点) in chapters."""

    def __init__(self, db: ReadingPowerDB) -> None:
        self.db = db

    def track(self, chapter: int, coolpoints: List[Dict[str, Any]]) -> None:
        """
        Store cool point data to database.

        Args:
            chapter: Chapter number
            coolpoints: List of cool point dictionaries with format:
                       [{"pattern": "装逼打脸", "density": 0.9, "combo_with": ["越级反杀"], "content": "..."}]
        """
        for cp in coolpoints:
            combo_str = (
                json.dumps(cp.get("combo_with", []), ensure_ascii=False)
                if cp.get("combo_with")
                else "[]"
            )

            self.db.save_coolpoint(
                chapter=str(chapter),
                pattern=cp["pattern"],
                density=cp.get("density", 0.5),
                combo_with=combo_str,
                content=cp.get("content", ""),
                llm_analyzed=cp.get("llm_analyzed", False),
            )

    def get_coolpoints(self, chapter: int) -> List[Dict[str, Any]]:
        """Get all cool points for a chapter."""
        coolpoints = self.db.get_coolpoints(str(chapter))
        for cp in coolpoints:
            if cp.get("combo_with"):
                try:
                    cp["combo_with"] = json.loads(cp["combo_with"])
                except (json.JSONDecodeError, TypeError):
                    cp["combo_with"] = []
        return coolpoints

    def get_coolpoint_summary(self, chapter: int) -> Dict[str, Any]:
        """Get cool point summary for a chapter."""
        coolpoints = self.get_coolpoints(chapter)
        if not coolpoints:
            return {"count": 0, "avg_density": 0.0, "patterns": []}

        patterns = [c["pattern"] for c in coolpoints]
        avg_density = sum(c["density"] for c in coolpoints) / len(coolpoints)

        return {
            "count": len(coolpoints),
            "avg_density": avg_density,
            "patterns": list(set(patterns)),
        }

    def get_combo_pairs(self, chapter: int) -> List[Tuple[str, str]]:
        """Get cool point combo pairs from a chapter."""
        coolpoints = self.get_coolpoints(chapter)
        pairs = []
        for cp in coolpoints:
            for combo in cp.get("combo_with", []):
                pairs.append((cp["pattern"], combo))
        return pairs
