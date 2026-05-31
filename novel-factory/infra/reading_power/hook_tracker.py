"""
HookTracker for the reading power system (追读力系统).
Tracks and retrieves reading hooks from chapters.
"""

from typing import List, Dict, Any

from infra.reading_power.db import ReadingPowerDB


class HookTracker:
    """Tracker for reading hooks (钩子) in chapters."""

    def __init__(self, db: ReadingPowerDB) -> None:
        self.db = db

    def track(self, chapter: int, hooks: List[Dict[str, Any]]) -> None:
        """
        Store hook data to database.

        Args:
            chapter: Chapter number
            hooks: List of hook dictionaries with format:
                  [{"type": "危机钩", "strength": 0.8, "position": "结尾", "content": "..."}]
        """
        for hook in hooks:
            self.db.save_hook(
                chapter=str(chapter),
                hook_type=hook["type"],
                strength=hook.get("strength", 0.5),
                position=hook.get("position", "中段"),
                content=hook.get("content", ""),
                llm_analyzed=hook.get("llm_analyzed", False),
            )

    def get_hooks(self, chapter: int) -> List[Dict[str, Any]]:
        """Get all hooks for a chapter."""
        return self.db.get_hooks(str(chapter))

    def get_hook_summary(self, chapter: int) -> Dict[str, Any]:
        """Get hook summary for a chapter."""
        hooks = self.get_hooks(chapter)
        if not hooks:
            return {"count": 0, "avg_strength": 0.0, "types": []}

        types = [h["hook_type"] for h in hooks]
        avg_strength = sum(h["strength"] for h in hooks) / len(hooks)

        return {
            "count": len(hooks),
            "avg_strength": avg_strength,
            "types": list(set(types)),
        }

    def get_all_hooks_by_type(
        self, hook_type: str, start_chapter: int = 1, end_chapter: int = 9999
    ) -> List[Dict[str, Any]]:
        """Get all hooks of a specific type within chapter range."""
        conn = self.db._get_connection()
        try:
            rows = conn.execute(
                """
                SELECT * FROM hooks
                WHERE hook_type = ? AND chapter >= ? AND chapter <= ?
                ORDER BY chapter
                """,
                (hook_type, str(start_chapter), str(end_chapter)),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()